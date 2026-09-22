"""反事实推理：回答"假如 A 没有发生，B 会怎样？"

推荐实现路线：
1. 删边模拟（ablation）：在图上临时移除"原因 A -> 结果 B"的因果边，
   重新计算 B 的可达原因集合，对比原图差异，推断 B 是否仍会发生；
2. 生成式（model）：基于证据链组织上下文，交给 LLM 做受控反事实推演，
   输出必须仍受图中证据约束。

证据约束：反事实结论需说明"在移除 X 后，沿哪些路径仍可达 / 不可达"。
"""
from __future__ import annotations

from ..common.schemas import Answer, CausalGraph, Query


def answer_counterfactual(graph: CausalGraph, query: Query, config=None) -> Answer:
    # TODO(成员 C)：删边模拟或生成式反事实推演，回填 evidence_chain。
    return Answer(
        query_id=query.query_id,
        question_type="counterfactual",
        answer_text="（占位）反事实推理结果",
        evidence_chain=[],
        confidence=0.0,
    )
