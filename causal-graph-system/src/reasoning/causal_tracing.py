"""因果追溯：回答"什么导致了 X？"（回溯）或 "X 会导致什么？"（前瞻）。

方法（多原因 + 多条因果链）：
- 枚举目标事件的**所有上游原因**，每个原因给出到目标的一条完整因果链，按强度排序；
- 区分直接原因 / 根本原因（入度为 0 的根事件）；
- 对直接原因做必要性（PN，级联语义）判定，标注"必要原因"；
- 前瞻同理：枚举所有下游后果，给出多条影响链 + 最终后果；
- 证据链 = 最强因果链上的边 id 有序序列。

参考：Pearl 结构因果模型（SCM）、Halpern-Pearl 实际因果（actual cause）定义。
"""
from __future__ import annotations

from ..common.schemas import Answer, CausalGraph, Query
from ..graph import to_networkx
from . import graph_algorithms as ga
from .evidence_chain import find_mentioned_events

_BACKWARD_CUES = ["什么导致", "是什么导致", "为什么", "的原因", "起因", "因为什么", "由于什么", "怎么造成"]
_FORWARD_CUES = ["导致", "引发", "造成", "引起", "会怎么样", "会怎样", "可能", "接下来", "后果"]

_MAX_CHAINS = 15


def _direction(question: str) -> str:
    for w in _BACKWARD_CUES:
        if w in question:
            return "backward"
    for w in _FORWARD_CUES:
        if w in question:
            return "forward"
    return "backward"


def _cfg_int(config, key: str, default: int) -> int:
    if config is None:
        return default
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def answer_causal_tracing(graph: CausalGraph, query: Query, config=None) -> Answer:
    G = to_networkx(graph)
    node_map = graph.node_map()
    max_depth = _cfg_int(config, "reasoning.causal_tracing.max_depth", 5)
    mentioned = find_mentioned_events(graph, query.question, limit=1)
    if not mentioned:
        return Answer(query_id=query.query_id, question_type="causal_tracing",
                      answer_text="未在图中定位到与问题相关的事件。",
                      evidence_chain=[], confidence=0.0)

    target = mentioned[0]
    tid = target.event_id
    direction = _direction(query.question)

    if direction == "backward":
        chains = ga.cause_chains(G, tid, max_depth)
        if not chains:
            text = f"「{target.mention}」在图中没有上游原因（可能是根事件）。"
            return Answer(query_id=query.query_id, question_type="causal_tracing",
                          answer_text=text, evidence_chain=[], confidence=0.0)

        direct = [n for n in G.predecessors(tid)]
        probs = ga.upstream_probabilities(G, tid, max_depth)
        root_causes = [n for n in probs if G.in_degree(n) == 0]

        lines = []
        if direct:
            items = []
            for n in direct:
                p = probs.get(n, ga.edge_confidence(G, n, tid))
                pn, _ = ga.necessity(G, n, tid, max_depth)
                tag = "，且为其必要原因" if pn >= 0.5 else ""
                items.append(f"{node_map[n].mention}（强度{p:.2f}{tag}）")
            lines.append("直接原因：" + "、".join(items))

        shown = ga.describe_chains(G, chains, node_map, _MAX_CHAINS)
        lines.append("多条因果链（按强度排序）：\n" + "\n".join(f"  · {s}" for s in shown))
        if len(chains) > _MAX_CHAINS:
            lines.append(f"  （另有 {len(chains) - _MAX_CHAINS} 条未列出）")

        if root_causes:
            lines.append("根本原因（根事件）：" + "、".join(
                f"{node_map[n].mention}" for n in sorted(root_causes, key=lambda n: -probs[n])))

        text = f"「{target.mention}」的因果追溯如下：\n" + "\n".join(lines)
        top_prob, top_path = chains[0]
        chain = ga.edge_ids(G, top_path)
        return Answer(query_id=query.query_id, question_type="causal_tracing",
                      answer_text=text, evidence_chain=chain,
                      confidence=round(min(top_prob, 0.99), 4),
                      metadata={"direction": direction, "target_event_id": tid,
                                "max_depth": max_depth, "chain_count": len(chains)})

    # ---- 前瞻 ----
    chains = ga.effect_chains(G, tid, max_depth)
    if not chains:
        text = f"「{target.mention}」在图中没有下游影响（可能是末端事件）。"
        return Answer(query_id=query.query_id, question_type="causal_tracing",
                      answer_text=text, evidence_chain=[], confidence=0.0)

    direct = list(G.successors(tid))
    probs = ga.downstream_probabilities(G, tid, max_depth)
    terminal = [n for n in probs if G.out_degree(n) == 0]

    lines = []
    if direct:
        lines.append("直接后果：" + "、".join(
            f"{node_map[n].mention}（强度{probs.get(n, ga.edge_confidence(G, tid, n)):.2f}）"
            for n in direct))

    shown = ga.describe_chains(G, chains, node_map, _MAX_CHAINS)
    lines.append("多条影响链（按强度排序）：\n" + "\n".join(f"  · {s}" for s in shown))
    if len(chains) > _MAX_CHAINS:
        lines.append(f"  （另有 {len(chains) - _MAX_CHAINS} 条未列出）")

    if terminal:
        lines.append("最终后果：" + "、".join(
            f"{node_map[n].mention}（强度{probs[n]:.2f}）"
            for n in sorted(terminal, key=lambda n: -probs[n])))

    text = f"「{target.mention}」可能引发的后续如下：\n" + "\n".join(lines)
    top_prob, top_path = chains[0]
    chain = ga.edge_ids(G, top_path)
    return Answer(query_id=query.query_id, question_type="causal_tracing",
                  answer_text=text, evidence_chain=chain,
                  confidence=round(min(top_prob, 0.99), 4),
                  metadata={"direction": direction, "target_event_id": tid,
                            "max_depth": max_depth, "chain_count": len(chains)})
