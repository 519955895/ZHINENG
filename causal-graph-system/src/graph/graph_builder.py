"""模块3 主接口：由事件 + 因果对构建因果图谱。

成员 C 请在此实现核心逻辑：
    build_graph(events, relations) -> CausalGraph
    to_networkx(graph) -> nx.DiGraph   （供推理问答做路径检索）

推荐实现要点：
1. 节点去重/归一化：同一事件可能被多次抽取，需按 mention 相似度合并；
2. 边构建：把 CausalRelation 转成有向边，处理冲突边（多策略见 config）；
3. 提供 networkx 视图：图遍历、最短路径、可达性、强连通分量等算法都基于它；
4. 元信息：统计节点数/边数/密度，便于后续诊断与可视化。
"""
from __future__ import annotations

from typing import List

from ..common.schemas import CausalGraph, CausalRelation, Event

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None


def build_graph(events: List[Event], relations: List[CausalRelation]) -> CausalGraph:
    """把事件节点与因果边组装为因果图。

    Args:
        events: 事件列表（作为节点）。
        relations: 因果对列表（作为有向边）。

    Returns:
        CausalGraph，graph_id 建议 "G" + 时间戳或自增序号。
    """
    # TODO(成员 C)：替换为真实建图逻辑（含节点去重、冲突边处理）。
    raise NotImplementedError("build_graph 尚未实现，请成员 C 在 graph_builder.py 中完成。")


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
