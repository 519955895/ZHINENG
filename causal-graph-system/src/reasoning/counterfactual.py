"""反事实推理：回答"假如 A 没有发生，B 会怎样？"

方法（级联消去 + PN/PS/PNS 概率因果）：
- 干预 do(A=0) 后做**级联消去**：把"只依赖 A、随 A 消失而连带消失"的节点全部找出；
- 两事件 A→B：估计 PN（必要性）、PS（充分性）、PNS（必要且充分），
  给出"删除 A 后 B 是否仍存活、有哪些连带消失节点、替代路径是什么"的对比；
- 单事件 A：给出删除 A 后连带消失的节点集，及其对最终结果（末端事件）的影响。

参考：Pearl 三阶因果层级与 twin-network 反事实、Balke-Pearl 反事实概率、
Tian-Pearl 的 PN/PS/PNS 概率因果。
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


def _ordered(node_ids, graph) -> list:
    order = {n.event_id: i for i, n in enumerate(graph.nodes)}
    return sorted(node_ids, key=lambda x: order.get(x, 0))


def _mentions(node_ids, node_map) -> str:
    return "、".join(node_map[n].mention for n in node_ids)


def answer_counterfactual(graph: CausalGraph, query: Query, config=None) -> Answer:
    G = to_networkx(graph)
    node_map = graph.node_map()
    max_depth = _cfg_int(config, "reasoning.counterfactual.max_depth", 5)
    mentioned = find_mentioned_events(graph, query.question)

    if not mentioned:
        return Answer(query_id=query.query_id, question_type="counterfactual",
                      answer_text="未在图中定位到相关事件。",
                      evidence_chain=[], confidence=0.0)

    cause = mentioned[0]
    alive, dead = ga.cascade_removal(G, cause.event_id)
    cascaded = [n for n in _ordered(dead, graph) if n != cause.event_id]

    # ---- 只定位到 A：回答"若 A 未发生，哪些事件会连带消失" ----
    if len(mentioned) == 1:
        if not cascaded:
            text = f"「{cause.mention}」在图中没有只依赖它的下游事件，删除它不影响其它事件。"
            return Answer(query_id=query.query_id, question_type="counterfactual",
                          answer_text=text, evidence_chain=[], confidence=0.0)

        # 连带消失节点里，哪些是"最终结果"（末端事件）
        dead_terminal = [n for n in cascaded if G.out_degree(n) == 0]
        alive_terminal = [n for n in _ordered(alive, graph) if G.out_degree(n) == 0]

        lines = [f"若「{cause.mention}」没有发生，将**连带消失**的事件为："
                 f"{_mentions(cascaded, node_map)}。"]
        if dead_terminal:
            lines.append(f"其中原本的最终结果「{_mentions(dead_terminal, node_map)}」将不再发生。")
        if alive_terminal:
            lines.append(f"仍有其它起因、不受影响的最终结果：「{_mentions(alive_terminal, node_map)}」。")

        # 证据链：取指向"最强连带消失节点"的因果链
        chain = []
        chains = ga.effect_chains(G, cause.event_id, max_depth)
        for prob, path in chains:
            if path[-1] in dead:
                chain = ga.edge_ids(G, path)
                break

        return Answer(query_id=query.query_id, question_type="counterfactual",
                      answer_text="\n".join(lines), evidence_chain=chain,
                      confidence=round(min(0.9, 0.99), 4),
                      metadata={"cause_event_id": cause.event_id,
                                "cascaded_ids": cascaded,
                                "alive_ids": _ordered(alive, graph)})

    # ---- 两个事件 A、B：级联消去 + PN/PS/PNS ----
    effect = mentioned[1]
    if cause.event_id == effect.event_id:
        text = "假设事件与结果事件相同，无法进行反事实比较。"
        return Answer(query_id=query.query_id, question_type="counterfactual",
                      answer_text=text, evidence_chain=[], confidence=0.0)

    pn, alt_path = ga.necessity(G, cause.event_id, effect.event_id, max_depth)
    ps = ga.sufficiency(G, cause.event_id, effect.event_id, max_depth)
    pns_val = pn * ps

    has_chain = ga.best_path(G, cause.event_id, effect.event_id, max_depth)
    chain = ga.edge_ids(G, has_chain[1]) if has_chain else []

    # 有 A 的情况
    if has_chain:
        with_a = (f"图中「{cause.mention}」→「{effect.mention}」存在因果路径"
                  f"（最可能路径联合置信度 {ps:.2f}）")
    else:
        with_a = f"图中「{cause.mention}」并非「{effect.mention}」的直接或间接原因"

    # 无 A 的情况（级联消去后 effect 是否存活）
    if effect.event_id in dead:
        no_a = (f"移除「{cause.mention}」后，「{effect.mention}」随级联一并消失，"
                f"将不再发生（无替代因果路径）")
    elif pn <= 0.05:
        no_a = (f"移除「{cause.mention}」后，「{effect.mention}」仍会发生"
                f"（存在替代路径，剩余强度 {1 - pn:.2f}）")
    else:
        no_a = (f"移除「{cause.mention}」后，「{effect.mention}」仍可能经其它路径发生"
                f"（剩余强度 {1 - pn:.2f}）")

    lines = [f"反事实「若 {cause.mention} 未发生」：{with_a}；{no_a}。",
             f"必要性 PN≈{pn:.2f}，充分性 PS≈{ps:.2f}，必要且充分 PNS≈{pns_val:.2f}。"]
    if cascaded:
        lines.append(f"连带消失的事件：{_mentions(cascaded, node_map)}。")
    if alt_path:
        lines.append(f"替代路径为：{ga.describe_path(G, alt_path, node_map)}。")

    return Answer(query_id=query.query_id, question_type="counterfactual",
                  answer_text="\n".join(lines), evidence_chain=chain,
                  confidence=round(min(max(ps, pn), 0.99), 4),
                  metadata={"cause_event_id": cause.event_id,
                            "effect_event_id": effect.event_id,
                            "PN": round(pn, 4), "PS": round(ps, 4),
                            "PNS": round(pns_val, 4),
                            "cascaded_ids": cascaded,
                            "alive_ids": _ordered(alive, graph)})
