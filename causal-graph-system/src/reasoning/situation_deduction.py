"""态势推演：回答"X 可能引发什么后续？"（前向多跳情景推演）。

方法（概率情景树，完整分支）：
- 从种子事件出发，沿因果边前向展开**所有后继分支**，构建一棵"可能性的树"；
- 每层节点的概率 = 父节点概率 × 边置信度（链式传播，独立性近似）；
- 分叉处每条分支都保留，同一事件出现在不同分支代表不同演化路径；
- 另给出"最可能的最终态势"（末端事件按概率排序）。

参考：贝叶斯网信念传播（belief propagation）、Endsley 态势感知"投影"层、
事件演化树 / 情景树（scenario tree）。
"""
from __future__ import annotations

from ..common.schemas import Answer, CausalGraph, Query
from ..graph import to_networkx
from . import graph_algorithms as ga
from .evidence_chain import find_mentioned_events


def _cfg_int(config, key: str, default: int) -> int:
    if config is None:
        return default
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _most_likely_terminal(G, tree, node_map):
    """在情景树里找累计概率最高的末端节点（无孩子）及其路径概率。"""
    best_node, best_prob = None, -1.0
    stack = [tree]
    while stack:
        t = stack.pop()
        children = t.get("children", [])
        if not children:
            if t["prob"] > best_prob:
                best_node, best_prob = t["node"], t["prob"]
        stack.extend(children)
    return best_node, best_prob


def answer_situation_deduction(graph: CausalGraph, query: Query, config=None) -> Answer:
    G = to_networkx(graph)
    node_map = graph.node_map()
    max_hops = _cfg_int(config, "reasoning.situation_deduction.max_hops", 3)
    mentioned = find_mentioned_events(graph, query.question, limit=1)
    if not mentioned:
        return Answer(query_id=query.query_id, question_type="situation_deduction",
                      answer_text="未在图中定位到与问题相关的事件。",
                      evidence_chain=[], confidence=0.0)

    target = mentioned[0]
    tid = target.event_id

    if G.out_degree(tid) == 0:
        text = f"「{target.mention}」在图中没有下游事件，暂无法推演后续态势。"
        return Answer(query_id=query.query_id, question_type="situation_deduction",
                      answer_text=text, evidence_chain=[], confidence=0.0)

    tree = ga.scenario_tree(G, tid, max_hops)
    tree_text = ga.render_scenario_tree(tree, node_map)

    terminal, terminal_prob = _most_likely_terminal(G, tree, node_map)

    lines = [f"从「{target.mention}」出发的可能性树（每层概率 = 上层概率 × 边置信度）：",
             tree_text]
    if terminal is not None:
        lines.append(f"最可能的最终态势：「{node_map[terminal].mention}」（概率 {terminal_prob:.2f}）")

    text = "\n".join(lines)

    # 证据链：取"最可能最终态势"对应的最强路径（若树里无末端，退化为最强单步）
    chain = []
    if terminal is not None:
        bp = ga.best_path(G, tid, terminal, max_hops)
        if bp:
            chain = ga.edge_ids(G, bp[1])
    if not chain:
        bp = ga.best_path(G, tid, list(G.successors(tid))[0], max_hops)
        if bp:
            chain = ga.edge_ids(G, bp[1])

    confidence = terminal_prob if terminal_prob > 0 else 0.0
    return Answer(query_id=query.query_id, question_type="situation_deduction",
                  answer_text=text, evidence_chain=chain,
                  confidence=round(min(confidence, 0.99), 4),
                  metadata={"target_event_id": tid, "max_hops": max_hops,
                            "tree": tree})
