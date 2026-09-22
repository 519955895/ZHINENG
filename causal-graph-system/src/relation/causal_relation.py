"""模块2 主接口：识别事件间的因果关系。

成员 B 请在此实现核心逻辑，只需保证函数签名与返回类型不变：
    extract_relations(events: List[Event]) -> List[CausalRelation]

推荐实现路线（渐进式）：
1. 基线：因果提示词（"导致/引起/因为/致使/造成/引发"）规则匹配，
   结合共现窗口（同句/同段/时间先后）形成候选对；
2. 升级 1：二分类判别模型（BERT 等）判断候选对是否为因果关系；
3. 升级 2：生成式 LLM 少样本抽取，直接输出 (cause, effect, type, evidence)；
4. 进阶：跨句/跨文档因果、隐式因果（无提示词）、时序约束（因先于果）。

输出约束：
- relation_id 全局唯一（建议 "R" + 自增序号）；
- cause/effect 必须是已有 event_id；
- evidence 必须回填原文证据片段（引用 mention），保证可解释性。
"""
from __future__ import annotations

from typing import List

from ..common.schemas import CausalRelation, Event


def extract_relations(events: List[Event]) -> List[CausalRelation]:
    """识别事件两两之间的因果关系。

    Args:
        events: 事件列表（模块1产出或赛题提供）。

    Returns:
        CausalRelation 列表，每条为一条有向因果边。
    """
    # TODO(成员 B)：替换为真实因果识别逻辑。
    raise NotImplementedError("extract_relations 尚未实现，请成员 B 在 causal_relation.py 中完成。")
