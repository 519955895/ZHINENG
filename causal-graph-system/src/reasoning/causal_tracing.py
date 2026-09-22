"""因果追溯：回答"什么导致了 X？" / "X 会导致什么？"

核心是图上的因果链检索：
- 回溯（backward）：找 X 的所有上游原因链（前驱路径）；
- 前瞻（forward）：找 X 的所有下游影响链（后继路径）。
用 networkx 的路径/可达性算法实现，证据链即命中的边 id 序列。
"""
from __future__ import annotations

from ..common.schemas import Answer, CausalGraph, Query


def answer_causal_tracing(graph: CausalGraph, query: Query, config=None) -> Answer:
    # TODO(成员 C)：基于 to_networkx(graph) 做前驱/后继路径检索，回填 evidence_chain。
    return Answer(
        query_id=query.query_id,
        question_type="causal_tracing",
        answer_text="（占位）因果追溯结果",
        evidence_chain=[],
        confidence=0.0,
    )
