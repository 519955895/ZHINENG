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

STATIC_DIR = os.path.join(BASE, "web", "static")
TESTSET_DIR = os.path.join(BASE, "eval", "testset")
GRAPHS_DIR = os.path.join(BASE, "data", "graphs")

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
