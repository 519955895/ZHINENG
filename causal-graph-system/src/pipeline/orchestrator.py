"""编排器：按 config 的 mode 串联各模块，覆盖三档难度。

三档数据流：
  challenge  : raw docs -> [模块1 抽取] -> events -> [模块2 关系] -> relations -> [模块3 建图] -> graph -> [推理]
  reasoning  :               events -> [模块2 关系] -> relations -> [模块3 建图] -> graph -> [推理]
  basic      :                                           graph -> [推理]

编排器只依赖各模块的**对外入口函数**，不关心内部实现，
因此三人可并行开发，只要入口签名不变即可无缝联调。
"""
from __future__ import annotations

import os
from typing import List, Optional

from ..common.config import Config, load_config, resolve_path
from ..common.io_utils import (
    load_documents,
    load_events,
    load_graph,
    load_relations,
    save_events,
    save_graph,
    save_relations,
)
from ..common.logger import get_logger
from ..common.schemas import (
    Answer,
    CausalGraph,
    CausalRelation,
    Document,
    Event,
    Query,
)
from ..extraction import extract_events
from ..graph import build_graph
from ..reasoning import answer_query
from ..relation import extract_relations

log = get_logger("pipeline")


def _load_queries(path: Optional[str]) -> List[Query]:
    """从 JSON 读取问题列表；无文件则返回空列表。"""
    if not path or not os.path.exists(path):
        return []
    import json
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Query.from_dict(q) for q in data]


def _save_answers(answers: List[Answer], out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    import json
    path = os.path.join(out_dir, "answers.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump([a.to_dict() for a in answers], f, ensure_ascii=False, indent=2)
    log.info("已写出 %d 条答案 -> %s", len(answers), path)


def run(config_path: str) -> List[Answer]:
    """按配置文件运行对应档位的完整流水线，返回答案列表。"""
    cfg = load_config(config_path)
    root = os.path.dirname(os.path.dirname(os.path.abspath(config_path)))  # 项目根目录
    mode = cfg.get("mode", "challenge")
    log.info("=== 启动流水线：mode=%s, level=%s ===", mode, cfg.get("level", "?"))

    graph: Optional[CausalGraph] = None

    # ---- 挑战档：从原始文档起步 ----
    if mode == "challenge":
        docs_path = resolve_path(root, cfg.get("paths.input_docs"))
        events_out = resolve_path(root, cfg.get("paths.events_out"))
        relations_out = resolve_path(root, cfg.get("paths.relations_out"))
        graph_out = resolve_path(root, cfg.get("paths.graph_out"))

        docs: List[Document] = load_documents(docs_path)
        log.info("模块1：事件抽取，文档 %d 篇", len(docs))
        events: List[Event] = extract_events(docs)
        save_events(events, events_out)

        log.info("模块2：因果识别，事件 %d 个", len(events))
        relations: List[CausalRelation] = extract_relations(events)
        save_relations(relations, relations_out)

        log.info("模块3：图谱构建")
        graph = build_graph(events, relations)
        save_graph(graph, graph_out)

    # ---- 推理档：从事件列表起步 ----
    elif mode == "reasoning":
        events_path = resolve_path(root, cfg.get("paths.input_events"))
        relations_out = resolve_path(root, cfg.get("paths.relations_out"))
        graph_out = resolve_path(root, cfg.get("paths.graph_out"))

        events = load_events(events_path)
        log.info("模块2：因果识别，事件 %d 个", len(events))
        relations = extract_relations(events)
        save_relations(relations, relations_out)

        log.info("模块3：图谱构建")
        graph = build_graph(events, relations)
        save_graph(graph, graph_out)

    # ---- 基础档：直接从因果图起步 ----
    elif mode == "basic":
        graph_path = resolve_path(root, cfg.get("paths.input_graph"))
        graph = load_graph(graph_path)
        log.info("基础档：直接载入因果图，节点 %d，边 %d", len(graph.nodes), len(graph.edges))

    else:
        raise ValueError(f"未知 mode：{mode}")

    # ---- 推理问答（三档共用）----
    queries_path = resolve_path(root, cfg.get("paths.queries"))
    queries = _load_queries(queries_path)
    log.info("推理问答：共 %d 个问题", len(queries))
    answers: List[Answer] = []
    for q in queries:
        ans = answer_query(graph, q, cfg)
        answers.append(ans)
        log.info("  [%s] %s", q.query_id, q.question_type)

    out_dir = resolve_path(root, cfg.get("paths.output_dir")) or "data/output/"
    _save_answers(answers, out_dir)
    log.info("=== 流水线结束 ===")
    return answers
