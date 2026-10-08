"""新闻事件因果图谱推理 —— 可视化前端后端服务。

零依赖（Python 标准库 http.server），实时调用已有推理逻辑。

接口：
  GET  /                 前端页面
  GET  /api/datasets     数据集列表（预置新闻测试集 + 因果图谱文件）
  POST /api/load         加载预置数据集   body: {"dataset_id": "news_01"}
  POST /api/upload       上传因果图谱 JSON body: {"graph": { ...CausalGraph 或 events+relations } }
  POST /api/query        三类推理问答     body: {"question": "...", "question_type": "causal_tracing"}

运行：py web/app.py   （默认 http://127.0.0.1:8000）
"""
import json
import os
import sys
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import networkx as nx  # noqa: E402

from src.common.schemas import CausalGraph, CausalRelation, Event, Query  # noqa: E402
from src.graph import build_graph, to_networkx  # noqa: E402
from src.reasoning import answer_query  # noqa: E402
from src.reasoning import graph_algorithms as ga  # noqa: E402
from src.competition.dataset import QUESTIONS_FILE, load_pack  # noqa: E402
from src.competition.runner import prepare_pack_graph  # noqa: E402
from src.competition.answering import answer_one  # noqa: E402

STATIC_DIR = os.path.join(BASE, "web", "static")
TESTSET_DIR = os.path.join(BASE, "eval", "testset")
GRAPHS_DIR = os.path.join(BASE, "data", "graphs")
DATASET_DIR = os.path.join(BASE, "data", "数据集")
TRAIN_DIR = os.path.join(DATASET_DIR, "训练集")
SAMPLE_DIR = os.path.join(DATASET_DIR, "抽样测试集_100")

# 竞赛包列表缓存：pack_id -> (pack_name, task, group, question_count)
_PACK_CACHE = None
_EVENTS_FILE = "事件列表.json"
_RELATIONS_FILE = "事件因果关系列表.json"

# 单用户内存态：当前加载的图谱
CURRENT = {"graph": None, "view": None, "analysis": None, "queries": [], "meta": {}}

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


# ---------------- 工具函数 ----------------
def _load_news(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    events = [Event.from_dict(e) for e in d["events"]]
    relations = [CausalRelation.from_dict(r) for r in d["relations"]]
    graph = build_graph(events, relations)
    queries = [Query.from_dict(q) for q in d.get("queries", [])]
    meta = {"news_id": d.get("news_id", ""), "title": d.get("title", ""),
            "source_url": d.get("source_url", ""), "domain": d.get("domain", ""),
            "date": d.get("date", "")}
    return graph, queries, meta


def _load_graph_file(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    graph = CausalGraph.from_dict(d)
    return graph, [], {"title": d.get("graph_id", os.path.basename(path))}


def to_echarts(graph: CausalGraph):
    G = to_networkx(graph)
    categories = sorted({n.event_type for n in graph.nodes if n.event_type})
    cat_map = {c: i for i, c in enumerate(categories)}
    max_deg = max([G.degree(n) for n in G.nodes], default=1) or 1
    nodes = []
    for n in graph.nodes:
        nodes.append({
            "id": n.event_id, "name": n.mention,
            "category": cat_map.get(n.event_type, 0),
            "symbolSize": round(26 + 22 * (G.degree(n.event_id) / max_deg), 1),
            "confidence": n.confidence, "event_type": n.event_type, "trigger": n.trigger,
        })
    links = []
    for e in graph.edges:
        links.append({
            "source": e.cause_event_id, "target": e.effect_event_id,
            "rid": e.relation_id, "relation_type": e.relation_type,
            "confidence": e.confidence, "evidence": e.evidence,
        })
    return {"categories": [{"name": c} for c in categories], "nodes": nodes, "links": links}


def analyze(graph: CausalGraph):
    G = to_networkx(graph)
    node_map = graph.node_map()
    pr = ga.pagerank(G)
    roots = [n for n in G.nodes if G.in_degree(n) == 0]
    leaves = [n for n in G.nodes if G.out_degree(n) == 0]
    top = sorted(pr.items(), key=lambda kv: -kv[1])[:3]
    return {
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "density": round(nx.density(G), 4),
        "roots": [{"id": n, "name": node_map[n].mention} for n in roots],
        "leaves": [{"id": n, "name": node_map[n].mention} for n in leaves],
        "max_in_degree": max([G.in_degree(n) for n in G.nodes], default=0),
        "max_out_degree": max([G.out_degree(n) for n in G.nodes], default=0),
        "relation_types": dict(Counter(e.relation_type for e in graph.edges)),
        "pagerank_top": [{"id": n, "name": node_map[n].mention, "score": round(s, 4)} for n, s in top],
    }


# ---------------- 路由处理 ----------------
def api_datasets():
    items = []
    if os.path.isdir(TESTSET_DIR):
        for fn in sorted(os.listdir(TESTSET_DIR)):
            if not fn.endswith(".json"):
                continue
            try:
                graph, queries, meta = _load_news(os.path.join(TESTSET_DIR, fn))
                items.append({"id": fn[:-5], "kind": "news", "title": meta.get("title") or fn[:-5],
                              "domain": meta.get("domain", ""), "node_count": len(graph.nodes),
                              "edge_count": len(graph.edges), "query_count": len(queries)})
            except Exception:  # noqa: BLE001
                pass
    if os.path.isdir(GRAPHS_DIR):
        for fn in sorted(os.listdir(GRAPHS_DIR)):
            if not fn.endswith(".json"):
                continue
            try:
                graph, _, _ = _load_graph_file(os.path.join(GRAPHS_DIR, fn))
                items.append({"id": "graph:" + fn[:-5], "kind": "graph", "title": fn[:-5],
                              "node_count": len(graph.nodes), "edge_count": len(graph.edges),
                              "query_count": 0})
            except Exception:  # noqa: BLE001
                pass
    return 200, items


def api_load(dataset_id):
    if not dataset_id:
        return 400, {"error": "缺少 dataset_id"}
    try:
        if dataset_id.startswith("graph:"):
            graph, queries, meta = _load_graph_file(os.path.join(GRAPHS_DIR, dataset_id[6:] + ".json"))
        else:
            graph, queries, meta = _load_news(os.path.join(TESTSET_DIR, dataset_id + ".json"))
    except FileNotFoundError:
        return 404, {"error": f"数据集不存在：{dataset_id}"}
    view = to_echarts(graph)
    analysis = analyze(graph)
    CURRENT.update(graph=graph, view=view, analysis=analysis,
                   queries=[q.to_dict() for q in queries], meta=meta)
    return 200, {"meta": meta, "view": view, "analysis": analysis, "queries": CURRENT["queries"]}


def api_upload(d):
    if "events" in d and "relations" in d:
        events = [Event.from_dict(e) for e in d["events"]]
        relations = [CausalRelation.from_dict(r) for r in d["relations"]]
        graph = build_graph(events, relations)
        title = d.get("news_id") or d.get("graph_id") or "上传图谱"
    else:
        graph = CausalGraph.from_dict(d)
        title = d.get("graph_id") or "上传图谱"
    view = to_echarts(graph)
    analysis = analyze(graph)
    CURRENT.update(graph=graph, view=view, analysis=analysis, queries=[], meta={"title": title})
    return 200, {"meta": CURRENT["meta"], "view": view, "analysis": analysis, "queries": []}


def api_query(question, question_type):
    if CURRENT["graph"] is None:
        return 400, {"error": "请先加载或上传图谱"}
    q = Query(query_id="UI", question=question, question_type=question_type)
    ans = answer_query(CURRENT["graph"], q)
    return 200, ans.to_dict()


# ---------------- 竞赛系统（模块1 事件抽取 / 模块2 关系获取 / 模块3 事实推理） ----------------
def _scan_packs():
    """扫描竞赛数据包：抽样集 A/B/C 全部 + 训练集小编号包（_0xx）。"""
    global _PACK_CACHE
    if _PACK_CACHE is not None:
        return _PACK_CACHE
    items = []

    def scan(root_dir, group, train_only_small=False):
        if not os.path.isdir(root_dir):
            return
        for dirpath, _dirs, files in os.walk(root_dir):
            if QUESTIONS_FILE not in files:
                continue
            name = os.path.basename(dirpath)
            if train_only_small:
                digits = "".join(ch for ch in name if ch.isdigit())
                if not digits or int(digits) >= 100:
                    continue
            if _RELATIONS_FILE in files:
                task = "A"
            elif _EVENTS_FILE in files:
                task = "B"
            else:
                task = "C"
            try:
                with open(os.path.join(dirpath, QUESTIONS_FILE), "r",
                          encoding="utf-8") as f:
                    qn = len(json.load(f))
            except Exception:  # noqa: BLE001
                qn = 0
            rel = os.path.relpath(dirpath, DATASET_DIR).replace(os.sep, "/")
            items.append({"id": rel, "name": name, "task": task,
                          "group": group, "question_count": qn})

    scan(SAMPLE_DIR, "抽样测试集")
    scan(TRAIN_DIR, "训练集（示例）", train_only_small=True)
    items.sort(key=lambda x: (x["group"], x["id"]))
    _PACK_CACHE = items
    return items


def api_comp_packs():
    return 200, _scan_packs()


def api_comp_run(pack_id):
    if not pack_id:
        return 400, {"error": "缺少 pack_id"}
    path = os.path.normpath(os.path.join(DATASET_DIR, *pack_id.split("/")))
    if not path.startswith(DATASET_DIR) or not os.path.isdir(path):
        return 404, {"error": f"数据包不存在：{pack_id}"}
    pack = load_pack(path)
    graph, events, relations = prepare_pack_graph(pack)
    doc_text = {d.doc_id: d.text for d in pack.docs}
    records = [answer_one(graph, q, task=pack.task, doc_text=doc_text)
               for q in pack.questions]
    view = to_echarts(graph)
    analysis = analyze(graph)
    CURRENT.update(graph=graph, view=view, analysis=analysis, queries=[],
                   meta={"title": pack.pack_name})
    refused = sum(1 for r in records if r.get("confidence_level") is None)
    modules = {
        "extraction": {
            "label": "模块1 · 事件抽取",
            "nodes": len(events),
            "source": "数据集给定标注" if pack.given_events else "系统抽取（文档→事件）",
            "active": not pack.given_events,
        },
        "relation": {
            "label": "模块2 · 关系获取",
            "edges": len(relations),
            "source": "数据集给定标注" if pack.given_relations else "系统获取（规则因果边）",
            "active": not pack.given_relations,
        },
        "reasoning": {
            "label": "模块3 · 事实推理",
            "questions": len(records), "refused": refused,
            "source": "系统答题引擎", "active": True,
        },
    }
    return 200, {
        "pack": {"name": pack.pack_name, "task": pack.task,
                 "doc_count": len(pack.docs), "question_count": len(records)},
        "modules": modules, "view": view, "analysis": analysis,
        "answers": records,
    }


# ---------------- HTTP handler ----------------
class Handler(BaseHTTPRequestHandler):
    server_version = "CausalGraphUI/1.0"

    def _send(self, status, payload, content_type="application/json; charset=utf-8"):
        if isinstance(payload, (dict, list)):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        else:
            body = payload
            content_type = "text/plain; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, rel):
        path = os.path.normpath(os.path.join(STATIC_DIR, rel))
        if not path.startswith(STATIC_DIR) or not os.path.isfile(path):
            return self._send(404, {"error": "not found"})
        ext = os.path.splitext(path)[1].lower()
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:  # noqa: BLE001
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self._serve_static("index.html")
        if path == "/api/datasets":
            status, payload = api_datasets()
            return self._send(status, payload)
        if path == "/api/competition/packs":
            status, payload = api_comp_packs()
            return self._send(status, payload)
        if path.startswith("/static/"):
            return self._serve_static(path[len("/static/"):])
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_json()
        if path == "/api/load":
            status, payload = api_load(data.get("dataset_id", ""))
        elif path == "/api/upload":
            status, payload = api_upload(data.get("graph", {}))
        elif path == "/api/query":
            status, payload = api_query(data.get("question", ""), data.get("question_type", ""))
        elif path == "/api/competition/run":
            status, payload = api_comp_run(data.get("pack_id", ""))
        else:
            status, payload = 404, {"error": "not found"}
        return self._send(status, payload)

    def log_message(self, fmt, *args):  # 精简日志
        sys.stderr.write("[%s] %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"因果图谱推理平台已启动：http://127.0.0.1:{port}  (Ctrl+C 退出)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出")
