"""模块3 主接口：图谱构建（成员 C，基线版）。

基线：直接以事件为节点、因果对为边。成员 C 可在此加入：
- 节点去重/合并（同一事件被多次抽取）；
- 冲突边处理（A→B 与 B→A）；
- 元信息统计（密度、出入度）。
"""
from __future__ import annotations

from typing import List

from ..common.schemas import CausalGraph, CausalRelation, Event

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None


def build_graph(events: List[Event], relations: List[CausalRelation]) -> CausalGraph:
    node_ids = {n.event_id for n in events}
    # 只保留两端节点都存在的边，避免悬空引用
    valid_edges = [r for r in relations
                   if r.cause_event_id in node_ids and r.effect_event_id in node_ids]
    graph = CausalGraph(
        graph_id="G001",
        nodes=list(events),
        edges=valid_edges,
        metadata={
            "node_count": len(events),
            "edge_count": len(valid_edges),
            "note": "基线建图：节点=事件，边=因果对，方向 cause -> effect",
        },
    )
    return graph


def to_networkx(graph: CausalGraph):
    """转换为 networkx 有向图，供路径检索等图算法使用。"""
    if nx is None:
        raise ImportError("networkx 未安装，请先 pip install networkx")
    g = nx.DiGraph()
    for node in graph.nodes:
        g.add_node(node.event_id, **node.to_dict())
    for edge in graph.edges:
        g.add_edge(
            edge.cause_event_id,
            edge.effect_event_id,
            relation_id=edge.relation_id,
            relation_type=edge.relation_type,
            confidence=edge.confidence,
            evidence=edge.evidence,
        )
    return g
