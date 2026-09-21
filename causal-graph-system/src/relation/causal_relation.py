"""模块2 主接口：规则版因果识别基线（成员 B）。

这是一个**可跑的基线**，用于打通全流程。成员 B 在此基础上升级即可
（函数签名不变）：
    extract_relations(events: List[Event]) -> List[CausalRelation]

基线思路（弱基线，先用起来）：
- 同一篇文档内、按阅读顺序相邻的事件对，视作因果候选（先发生的是因，后发生的是果）；
- 新闻叙事多为顺承，该启发在样例上效果尚可；
- evidence 暂用"因片段 -> 果片段"拼接，升级版应回填原文原句。

升级路线（见 docs/module2_relation.md）：
- 提示词规则（导致/造成/因为/致使…）做方向与类型判定；
- 判别式二分类（BERT）；生成式 LLM 少样本抽取，直接输出 evidence。
"""
from __future__ import annotations

from typing import Dict, List

from ..common.schemas import CausalRelation, Event, RELATION_CAUSAL


def _sort_key(e: Event) -> int:
    try:
        return int(e.event_id[1:])
    except (ValueError, IndexError):
        return 0


def extract_relations(events: List[Event]) -> List[CausalRelation]:
    by_doc: Dict[str, List[Event]] = {}
    for e in events:
        by_doc.setdefault(e.doc_id, []).append(e)
    for doc_events in by_doc.values():
        doc_events.sort(key=_sort_key)

    relations: List[CausalRelation] = []
    rid = 0
    for doc_events in by_doc.values():
        for cause, effect in zip(doc_events, doc_events[1:]):
            rid += 1
            relations.append(CausalRelation(
                relation_id=f"R{rid:03d}",
                cause_event_id=cause.event_id,
                effect_event_id=effect.event_id,
                relation_type=RELATION_CAUSAL,
                evidence=[f"{cause.mention} → {effect.mention}"],
                confidence=0.7,
                time_lag="immediate",
            ))
    return relations
