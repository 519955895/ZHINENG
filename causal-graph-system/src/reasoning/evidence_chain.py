"""证据链工具：把图上的边/节点 id 序列映射回原文证据片段。

成员 C 用它保证答案可解释、可追溯；也可供成员 A/B 自查。
"""
from __future__ import annotations

from typing import List

from ..common.schemas import CausalGraph


def collect_evidence(graph: CausalGraph, chain_ids: List[str]) -> List[str]:
    """按 id 序列收集原文证据片段。

    chain_ids 可混合边 id（relation_id）与节点 id（event_id）。
    返回对应 mention / evidence 文本列表。
    """
    evidence: List[str] = []
    edge_map = {e.relation_id: e for e in graph.edges}
    node_map = graph.node_map()
    for cid in chain_ids:
        if cid in edge_map:
            evidence.extend(edge_map[cid].evidence)
        elif cid in node_map:
            evidence.append(node_map[cid].mention)
    return evidence
