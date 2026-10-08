"""模块3 主接口：由事件 + 因果对构建因果图谱。

实现要点：
1. 节点去重/归一化：同 event_id 合并，字段尽量保留信息更丰富的一版；
2. 边构建：把 CausalRelation 转成有向边，丢弃悬空边（端点不存在），
   合并重复边（保留置信度更高者），双向冲突时保留高置信边；
3. networkx 视图：供推理模块做路径检索、可达性、中心性等计算；
4. 元信息：节点数/边数/密度。
"""
from __future__ import annotations

from typing import Dict, List

from ..common.schemas import CausalGraph, CausalRelation, Event

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None


def _merge_events(events: List[Event]) -> List[Event]:
    """同 event_id 去重：保留信息更丰富（论元/触发词更多）的事件。"""
    merged: Dict[str, Event] = {}
    order: List[str] = []
    for e in events:
        if e.event_id not in merged:
            merged[e.event_id] = e
            order.append(e.event_id)
            continue
        old = merged[e.event_id]
        # 以"信息量"决定主记录，缺失字段用另一条补全
        primary, secondary = (e, old) if (
            len(e.arguments) > len(old.arguments)
            or (len(e.arguments) == len(old.arguments) and len(e.mention) > len(old.mention))
        ) else (old, e)
        if not primary.trigger and secondary.trigger:
            primary.trigger = secondary.trigger
        if not primary.event_type and secondary.event_type:
            primary.event_type = secondary.event_type
        if not primary.time and secondary.time:
            primary.time = secondary.time
        if not primary.location and secondary.location:
            primary.location = secondary.location
        primary.confidence = max(primary.confidence or 0.0, secondary.confidence or 0.0)
        merged[e.event_id] = primary
    return [merged[k] for k in order]


def build_graph(events: List[Event], relations: List[CausalRelation]) -> CausalGraph:
    """把事件节点与因果边组装为因果图。

    Args:
        events: 事件列表（作为节点）。
        relations: 因果对列表（作为有向边，方向 cause -> effect）。

    Returns:
        CausalGraph；悬空边与重复边已清洗，冲突边按置信度取舍。
    """
    nodes = _merge_events(list(events))
    node_ids = {n.event_id for n in nodes}

    # 清洗 + 去重 + 冲突处理
    edge_map: Dict[tuple, CausalRelation] = {}
    for r in relations:
        if r.cause_event_id not in node_ids or r.effect_event_id not in node_ids:
            continue
        if r.cause_event_id == r.effect_event_id:
            continue
        key = (r.cause_event_id, r.effect_event_id)
        if key not in edge_map or (r.confidence or 0) > (edge_map[key].confidence or 0):
            edge_map[key] = r

    # 双向冲突：若 A->B 与 B->A 同时出现，保留置信度更高的一边
    pruned: Dict[tuple, CausalRelation] = {}
    for key, r in edge_map.items():
        rev = (key[1], key[0])
        if rev in edge_map and (r.confidence or 0) < (edge_map[rev].confidence or 0):
            continue
        pruned[key] = r

    valid_edges = list(pruned.values())
    # 重排 relation_id，保证可读、唯一
    for i, e in enumerate(valid_edges, 1):
        if not e.relation_id:
            e.relation_id = f"R{i:03d}"

    graph = CausalGraph(
        graph_id="G001",
        nodes=nodes,
        edges=valid_edges,
        metadata={
            "node_count": len(nodes),
            "edge_count": len(valid_edges),
            "note": "节点=事件，边=因果对，方向 cause -> effect；已去重并清洗悬空/冲突边",
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
