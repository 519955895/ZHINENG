"""模块3续：证据约束下的推理问答（成员 C）。

对外唯一入口：
    answer_query(graph, query, config) -> Answer
根据 query.question_type 分发到三类推理：
    - causal_tracing       因果追溯
    - situation_deduction  态势推演
    - counterfactual       反事实推理
"""
from __future__ import annotations

from ..common.schemas import (
    Answer,
    CausalGraph,
    QT_CAUSAL_TRACING,
    QT_COUNTERFACTUAL,
    QT_SITUATION_DEDUCTION,
    Query,
)
from .causal_tracing import answer_causal_tracing
from .situation_deduction import answer_situation_deduction
from .counterfactual import answer_counterfactual

_HANDLERS = {
    QT_CAUSAL_TRACING: answer_causal_tracing,
    QT_SITUATION_DEDUCTION: answer_situation_deduction,
    QT_COUNTERFACTUAL: answer_counterfactual,
}


def answer_query(graph: CausalGraph, query: Query, config=None) -> Answer:
    """按问题类型分发的统一推理入口。"""
    handler = _HANDLERS.get(query.question_type)
    if handler is None:
        return Answer(
            query_id=query.query_id,
            question_type=query.question_type,
            answer_text=f"暂不支持的问题类型：{query.question_type}",
            confidence=0.0,
        )
    return handler(graph, query, config)


__all__ = ["answer_query"]
