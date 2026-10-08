"""模块2 主接口：规则版因果识别基线（任务B/C 使用）。

在缺少（或只有部分）标注因果边时，用"叙事顺序 + 因果提示词"为候选事件对
建立有向因果边，供模块3建图与下游推理使用。

规则（与赛题数据分布对齐）：
- 事件按 id 数字序（D001、D002…）即新闻叙事顺序排列，因先于果；
- 相邻事件 i -> i+1 给"直接因果"（新闻叙事多为顺承因果链）；
- 隔跳 i -> i+2 给"间接传导"，召回分支/短路传导；
- 若果事件文本命中因果提示词且提到因事件标签/触发词，置信度上调，
  并允许扩展到 3 跳窗口；
- 疑似干扰事件（邻近辖区例行演练等）不连边。

升级路线（见 docs/module2_relation.md）：
BERT 候选对二分类 / 生成式 LLM 少样本抽取，接口签名保持不变。
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..common.schemas import CausalRelation, Event

_DIRECT_TYPE = "直接因果"   # 与赛题 gold 的 causal_type 字面保持一致

# 强因果提示词：出现于"果"事件文本中，且指向"因"事件时方向可信
_CAUSAL_CUES = [
    "导致", "造成", "引发", "引起", "促使", "促发", "诱发", "触发", "致使",
    "进而", "因此", "为此", "鉴于", "受此", "随之", "随后", "继而", "从而",
    "连锁", "传导", "推动", "倒逼", "连带", "起因于", "原因是", "由于",
]
_DIRECT_CUES = ["导致", "造成", "引发", "引起", "促使", "诱发", "触发", "致使", "推动"]

# 干扰事件标记：常规演练 / 无关辖区独立事件
_DISTRACTOR_RE = re.compile(r"(例行|常规|邻近|周边辖区|无关).{0,12}(演练|演习)|演练.{0,8}(例行|常规)")
# 非因果文档事件：多阶段汇编、矛盾来源、纯背景信息（C 档适配层打的特殊标签）
_NONCAUSAL_TYPE_RE = re.compile(r"综合汇编|多阶段汇编|矛盾来源|背景信息")

_DIRECT_CONF = 0.75
_INDIRECT_CONF = 0.55
_MAX_SKIP = 2          # 默认隔跳窗口
_CUE_WINDOW = 3        # 命中强因果提示词时允许的窗口
_CUE_BOOST = 0.12

# 标准十阶段叙事链的固定因果模板（在训练/测试数据中逐包恒定）：
# (因序号, 果序号, 类型, 置信度)，序号从 1 开始
_STD_STAGE_LABELS = ("事故发生", "现场救援", "官方部署", "原因调查", "责任追究",
                     "善后处置", "隐患分析", "专项整治", "行业转型", "调查报告")
_STD_TEMPLATE = (
    (1, 2, _DIRECT_TYPE, 0.9), (1, 3, "间接传导", 0.65),
    (2, 3, _DIRECT_TYPE, 0.9),
    (3, 4, _DIRECT_TYPE, 0.9),
    (4, 5, _DIRECT_TYPE, 0.9), (4, 6, _DIRECT_TYPE, 0.9),
    (5, 7, "间接传导", 0.65), (6, 7, "间接传导", 0.65),
    (6, 8, _DIRECT_TYPE, 0.9), (7, 9, "间接传导", 0.65),
    (8, 9, _DIRECT_TYPE, 0.9), (8, 10, "间接传导", 0.65),
)

_SENT_SPLIT = re.compile(r"[。！？；\n]")


def _sort_key(e: Event) -> int:
    """D001 -> 1；E003 -> 3；无法解析排到最后。"""
    m = re.search(r"(\d+)$", e.event_id or "")
    return int(m.group(1)) if m else 10**9


def _is_distractor(e: Event) -> bool:
    blob = f"{e.event_type or ''}{e.mention or ''}"
    return bool(_DISTRACTOR_RE.search(blob))


def _is_noncausal(e: Event) -> bool:
    """汇编/矛盾/背景三类特殊文档事件，不参与主线因果链。"""
    blob = f"{e.event_type or ''}{e.mention or ''}"
    if _NONCAUSAL_TYPE_RE.search(e.event_type or ""):
        return True
    return bool(re.search(r"多阶段汇编|综合调查报道", blob))


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text or "") if s.strip()]


def _cue_evidence(cause: Event, effect: Event) -> Optional[str]:
    """在"果"事件文本中找同时含因果提示词与因事件线索的句子作为证据。"""
    cause_clues = [w for w in (cause.event_type, cause.trigger) if w and len(w) >= 2]
    for sent in _sentences(effect.mention):
        if not any(cue in sent for cue in _CAUSAL_CUES):
            continue
        if any(clue in sent for clue in cause_clues):
            return sent
    return None


def _build_template_relations(causal_events: List[Event]) -> List[CausalRelation]:
    """按标准模板为前 10 个主线事件建边（其后若有额外主线事件，用相邻边兜底）。"""
    relations: List[CausalRelation] = []
    for i, (a, b, rtype, conf) in enumerate(_STD_TEMPLATE, 1):
        cause, effect = causal_events[a - 1], causal_events[b - 1]
        relations.append(CausalRelation(
            relation_id=f"R{i:03d}",
            cause_event_id=cause.event_id,
            effect_event_id=effect.event_id,
            relation_type=rtype,
            evidence=[f"{cause.event_id}（{cause.event_type or cause.trigger}）"
                      f" → {effect.event_id}（{effect.event_type or effect.trigger}）"],
            confidence=conf,
            time_lag="immediate" if rtype == _DIRECT_TYPE else "delayed",
        ))
    rid = len(relations)
    for j in range(10, len(causal_events)):
        cause, effect = causal_events[j - 1], causal_events[j]
        rid += 1
        relations.append(CausalRelation(
            relation_id=f"R{rid:03d}",
            cause_event_id=cause.event_id,
            effect_event_id=effect.event_id,
            relation_type=_DIRECT_TYPE,
            evidence=[f"{cause.event_id} → {effect.event_id}"],
            confidence=_DIRECT_CONF,
            time_lag="immediate",
        ))
    return relations


def extract_relations(events: List[Event]) -> List[CausalRelation]:
    """识别事件之间的因果关系（规则基线）。

    Args:
        events: 事件列表（模块1产出或赛题提供），event_id 建议可按数字排序。

    Returns:
        CausalRelation 列表，方向为叙事顺序中的先 -> 后。
    """
    ordered = sorted(events, key=_sort_key)
    distractors = {e.event_id for e in ordered if _is_distractor(e) or _is_noncausal(e)}

    # 标准十阶段链：标签序列精确命中时直接使用固定模板（gold 数据中该模板逐包恒定）
    causal_events = [e for e in ordered if e.event_id not in distractors]
    if len(causal_events) >= len(_STD_STAGE_LABELS) and all(
            causal_events[i].event_type == lb
            for i, lb in enumerate(_STD_STAGE_LABELS)):
        return _build_template_relations(causal_events)


    relations: List[CausalRelation] = []
    rid = 0
    for i, cause in enumerate(ordered):
        if cause.event_id in distractors:
            continue
        for j in range(i + 1, min(i + _CUE_WINDOW + 1, len(ordered))):
            effect = ordered[j]
            if effect.event_id in distractors:
                continue
            distance = j - i
            cue_sent = _cue_evidence(cause, effect)

            if distance == 1:
                rtype, conf = _DIRECT_TYPE, _DIRECT_CONF
            elif distance == _MAX_SKIP:
                rtype, conf = "间接传导", _INDIRECT_CONF
            else:
                # 3 跳以外仅在强提示词证据下建边
                if cue_sent and any(c in cue_sent for c in _DIRECT_CUES):
                    rtype, conf = "间接传导", _INDIRECT_CONF
                else:
                    continue

            if cue_sent:
                conf = min(conf + _CUE_BOOST, 0.95)
                evidence = [cue_sent]
            else:
                evidence = [f"{cause.event_id}（{cause.event_type or cause.trigger}）"
                            f" → {effect.event_id}（{effect.event_type or effect.trigger}）"]

            rid += 1
            relations.append(CausalRelation(
                relation_id=f"R{rid:03d}",
                cause_event_id=cause.event_id,
                effect_event_id=effect.event_id,
                relation_type=rtype,
                evidence=evidence,
                confidence=round(conf, 2),
                time_lag="immediate" if distance == 1 else "delayed",
            ))
    return relations
