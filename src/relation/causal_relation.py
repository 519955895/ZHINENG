"""模块2 主接口：识别事件间的因果关系（规则基线优化版 v2）。

成员 B 在此实现核心逻辑，函数签名与返回类型固定：
    extract_relations(events: List[Event], config=None) -> List[CausalRelation]

优化点（v2，全部纯规则、无需额外依赖）：
  1. 扩展配对范围：同文档内两两配对（不再仅相邻），提升召回率；
  2. 位置邻近性加权：用 char_offset 距离加分，原文越近置信度越高；
  3. 论元重叠检测：共享 subject/object/location 论元时加分；
  4. 时间约束强化：strict_temporal=True 时因晚于果直接丢弃，否则扣减；
  5. 提示词上下文验证：提示词附近无事件论元时降权；
  6. 配置化：阈值与开关可通过 config 参数覆盖，默认值内置。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from ..common.config import Config
from ..common.logger import get_logger
from ..common.schemas import CausalRelation, Event
from .cue_pattern import find_cues, select_best_cue

log = get_logger("relation")

# 默认配置（config 未传或字段缺失时使用）
DEFAULT_CONFIG: Dict[str, Any] = {
    "min_confidence": 0.30,      # 综合分阈值，低于此值不产出
    "strict_temporal": False,    # True=因晚于果直接丢弃；False=扣减 0.2
    "location_bonus": 0.10,      # 位置邻近性最大加分
    "argument_bonus": 0.10,      # 论元重叠最大加分
    "time_bonus": 0.05,          # 时间接近最大加分
    "context_penalty": 0.15,     # 提示词附近无论元时的扣减
    "margin_threshold": 0.15,    # 边际分差阈值，低于此值时降权
    # ---- ML 模式专用参数 ----
    "ml_proximity_threshold": 800,  # 无提示词时，只打分 char_offset 距离在此值内的事件对
    "ml_direction_margin": 0.05,     # 双向打分时，两方向概率差小于此值则丢弃（方向不确定）
}

# 特征加分总上限（各特征 bonus 之和不超过此值）
TOTAL_BONUS_CAP = 0.25


def apply_feature_weights(path: str) -> Dict[str, float]:
    """从 JSON 文件加载学习到的特征权重，更新 DEFAULT_CONFIG 中的 bonus。

    JSON 格式（标定工具输出）：
        {"cue_weight": 0.50, "location": 0.20, "argument": 0.20, "time_match": 0.10}
    这些是归一化后的相对权重（和为1），转换为：
        location_bonus = TOTAL_BONUS_CAP × location
        argument_bonus = TOTAL_BONUS_CAP × argument
        time_bonus     = TOTAL_BONUS_CAP × time_match

    Returns:
        更新后的 bonus 配置字典。
    """
    import json

    with open(path, "r", encoding="utf-8") as f:
        weights = json.load(f)

    DEFAULT_CONFIG["location_bonus"] = round(TOTAL_BONUS_CAP * weights.get("location", 0.2), 4)
    DEFAULT_CONFIG["argument_bonus"] = round(TOTAL_BONUS_CAP * weights.get("argument", 0.2), 4)
    DEFAULT_CONFIG["time_bonus"] = round(TOTAL_BONUS_CAP * weights.get("time_match", 0.1), 4)

    log.info(
        "已加载特征权重: location=%.4f, argument=%.4f, time=%.4f",
        DEFAULT_CONFIG["location_bonus"],
        DEFAULT_CONFIG["argument_bonus"],
        DEFAULT_CONFIG["time_bonus"],
    )
    return {
        "location_bonus": DEFAULT_CONFIG["location_bonus"],
        "argument_bonus": DEFAULT_CONFIG["argument_bonus"],
        "time_bonus": DEFAULT_CONFIG["time_bonus"],
    }


def _cfg(config: Optional[Config], key: str) -> Any:
    """从 config 取值，缺失则用默认值。"""
    if config is not None and isinstance(config, Config):
        val = config.get(f"relation.{key}", None)
        if val is not None:
            return val
    return DEFAULT_CONFIG[key]


def _sort_key(e: Event) -> Tuple[str, int]:
    """事件排序键：先按 time，再按 char_offset 起点。"""
    return (e.time or "", e.char_offset[0] if e.char_offset else 0)


def _char_distance(a: Event, b: Event) -> Optional[int]:
    """两事件在原文中的字符距离（取 char_offset 中点差），无 offset 时返回 None。"""
    if not a.char_offset or not b.char_offset:
        return None
    mid_a = (a.char_offset[0] + a.char_offset[1]) // 2
    mid_b = (b.char_offset[0] + b.char_offset[1]) // 2
    return abs(mid_a - mid_b)


def _shared_args(a: Event, b: Event) -> List[str]:
    """返回两事件共享的论元 value 列表。"""
    vals_a = {arg.value for arg in a.arguments}
    vals_b = {arg.value for arg in b.arguments}
    return list(vals_a & vals_b)


def _has_arg_near_cue(mention: str, cue_word: str, evt: Event) -> bool:
    """检查提示词附近是否有事件的论元 value（简单上下文验证）。"""
    if not evt.arguments:
        return True  # 无论元则不惩罚
    for arg in evt.arguments:
        if arg.value and arg.value in mention:
            return True
    return False


def _score_pair(
    cause_evt: Event,
    effect_evt: Event,
    cue_word: str,
    cue_weight: float,
    config: Optional[Config],
) -> float:
    """计算一对事件的综合置信度。

    综合分 = 提示词权重 + 归一化加分项 - 上下文惩罚。
    加分项上限为 cue_weight × 0.5，确保提示词权重占比 ≥ 2/3（避免"命中即高分"）。
    """
    score = cue_weight

    # ---- 位置邻近性加分 ----
    dist = _char_distance(cause_evt, effect_evt)
    location_pts = 0.0
    if dist is not None:
        max_bonus = float(_cfg(config, "location_bonus"))
        location_pts = max_bonus * max(0.0, 1.0 - dist / 500.0)

    # ---- 论元重叠加分 ----
    shared = _shared_args(cause_evt, effect_evt)
    argument_pts = 0.0
    if shared:
        max_bonus = float(_cfg(config, "argument_bonus"))
        argument_pts = max_bonus * min(1.0, len(shared) / 2.0)

    # ---- 时间接近加分 ----
    time_pts = 0.0
    if cause_evt.time and effect_evt.time:
        max_bonus = float(_cfg(config, "time_bonus"))
        common = 0
        for ca, cb in zip(cause_evt.time, effect_evt.time):
            if ca == cb:
                common += 1
            else:
                break
        time_pts = max_bonus * min(1.0, common / 10.0)

    # ---- 加分项归一化：总加分不超过 cue_weight 的 50% ----
    raw_bonus = location_pts + argument_pts + time_pts
    bonus_cap = cue_weight * 0.5
    bonus = min(raw_bonus, bonus_cap)
    score += bonus

    # ---- 提示词上下文验证：附近无论元则扣减 ----
    if not _has_arg_near_cue(effect_evt.mention, cue_word, effect_evt) and \
       not _has_arg_near_cue(cause_evt.mention, cue_word, cause_evt):
        score -= float(_cfg(config, "context_penalty"))

    return round(min(1.0, max(0.0, score)), 4)


def _build_evidence(cause_evt: Event, effect_evt: Event) -> List[str]:
    """拼接因果双方的 mention 作为证据链。"""
    seen: Set[str] = set()
    result: List[str] = []
    for m in (cause_evt.mention, effect_evt.mention):
        if m and m not in seen:
            seen.add(m)
            result.append(m)
    return result


def _extract_ml_batch(
    events: List[Event],
    config: Optional[Config],
    ml_scorer: Any,
) -> List[CausalRelation]:
    """ML 批量打分模式：先收集所有候选对，再一次性批量推理。

    与逐条 score() 结果等价，但利用 GPU 批量并行大幅加速。
    """
    min_conf = float(_cfg(config, "min_confidence"))
    strict_temp = bool(_cfg(config, "strict_temporal"))
    prox_threshold = float(_cfg(config, "ml_proximity_threshold"))
    direction_margin = float(_cfg(config, "ml_direction_margin"))

    # ---- 按文档分组 ----
    by_doc: Dict[str, List[Event]] = {}
    for e in events:
        by_doc.setdefault(e.doc_id, []).append(e)

    # ---- Phase 1: 收集所有需要 ML 打分的候选对 ----
    candidates: List[Dict[str, Any]] = []
    for doc_id, doc_events in by_doc.items():
        sorted_events = sorted(doc_events, key=_sort_key)
        n = len(sorted_events)

        for i in range(n):
            for j in range(i + 1, n):
                e_a = sorted_events[i]
                e_b = sorted_events[j]

                hits_a = find_cues(e_a.mention)
                hits_b = find_cues(e_b.mention)

                cue_candidates: List[Tuple[Event, Event, str, str, str, float]] = []
                for cue, rtype, direction, w in hits_a:
                    if direction == "backward":
                        cue_candidates.append((e_a, e_b, cue, rtype, direction, w))
                    else:
                        cue_candidates.append((e_b, e_a, cue, rtype, direction, w))
                for cue, rtype, direction, w in hits_b:
                    if direction == "forward":
                        cue_candidates.append((e_a, e_b, cue, rtype, direction, w))
                    else:
                        cue_candidates.append((e_b, e_a, cue, rtype, direction, w))

                if not cue_candidates:
                    # 无提示词：检查邻近性
                    dist = _char_distance(e_a, e_b)
                    if dist is not None and dist > prox_threshold:
                        continue
                    candidates.append({
                        "bidirectional": True,
                        "e_a": e_a, "e_b": e_b,
                    })
                else:
                    # 有提示词：选最优候选
                    consistent = [
                        c for c in cue_candidates
                        if not (c[0].time and c[1].time and c[0].time > c[1].time)
                    ]
                    pool = consistent if consistent else cue_candidates
                    pool_sorted = sorted(pool, key=lambda c: c[5], reverse=True)
                    best = pool_sorted[0]
                    cause_evt, effect_evt, cue_word, rtype, direction, weight = best

                    # 严格时序模式下提前过滤
                    if strict_temp and cause_evt.time and effect_evt.time \
                       and cause_evt.time > effect_evt.time:
                        continue

                    candidates.append({
                        "bidirectional": False,
                        "cause_evt": cause_evt,
                        "effect_evt": effect_evt,
                        "cue_word": cue_word,
                        "rtype": rtype,
                    })

    log.info("ML 批量模式：收集到 %d 个候选对", len(candidates))

    # ---- Phase 2: 构建打分列表 ----
    score_pairs: List[Tuple[str, str]] = []
    for c in candidates:
        if c["bidirectional"]:
            score_pairs.append((c["e_a"].mention, c["e_b"].mention))
            score_pairs.append((c["e_b"].mention, c["e_a"].mention))
        else:
            score_pairs.append((c["cause_evt"].mention, c["effect_evt"].mention))

    # ---- Phase 3: 批量打分 ----
    results = ml_scorer.score_batch(score_pairs)
    log.info("ML 批量打分完成，共 %d 次推理", len(results))

    # ---- Phase 4: 处理结果，构建关系 ----
    relations: List[CausalRelation] = []
    seen_pairs: Set[Tuple[str, str]] = set()
    rid = 0
    idx = 0

    for c in candidates:
        if c["bidirectional"]:
            prob_fwd, _ = results[idx]
            prob_bwd, _ = results[idx + 1]
            idx += 2

            # 两方向概率都很低 → 非因果
            if prob_fwd < min_conf and prob_bwd < min_conf:
                continue
            # 方向不确定 → 丢弃
            if abs(prob_fwd - prob_bwd) < direction_margin:
                log.debug(
                    "方向不确定：%s<->%s (fwd=%.3f, bwd=%.3f)",
                    c["e_a"].event_id, c["e_b"].event_id, prob_fwd, prob_bwd,
                )
                continue
            # 取概率高的方向
            if prob_fwd >= prob_bwd:
                cause_evt, effect_evt = c["e_a"], c["e_b"]
                ml_prob = prob_fwd
            else:
                cause_evt, effect_evt = c["e_b"], c["e_a"]
                ml_prob = prob_bwd
            ml_type = "causal"
            cue_word = ""
        else:
            ml_prob, ml_type = results[idx]
            idx += 1
            cause_evt = c["cause_evt"]
            effect_evt = c["effect_evt"]
            cue_word = c["cue_word"]

        # 时序校验（非严格模式下也跳过明显违例）
        if cause_evt.time and effect_evt.time and cause_evt.time > effect_evt.time:
            if strict_temp:
                continue

        if ml_type == "none" or ml_prob < min_conf:
            log.debug(
                "ML 判定无因果：%s -> %s (prob=%.3f, type=%s)",
                cause_evt.event_id, effect_evt.event_id, ml_prob, ml_type,
            )
            continue

        confidence = round(min(1.0, max(0.0, ml_prob)), 4)
        rtype = ml_type

        # 去重
        pair = (cause_evt.event_id, effect_evt.event_id)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        rid += 1
        relations.append(
            CausalRelation(
                relation_id=f"R{rid:03d}",
                cause_event_id=cause_evt.event_id,
                effect_event_id=effect_evt.event_id,
                relation_type=rtype,
                evidence=_build_evidence(cause_evt, effect_evt),
                confidence=round(confidence, 2),
            )
        )
        log.debug(
            "产出 %s: %s -> %s [%s] conf=%.2f (cue='%s')",
            f"R{rid:03d}", cause_evt.event_id, effect_evt.event_id,
            rtype, confidence, cue_word,
        )

    return relations


def extract_relations(
    events: List[Event],
    config: Optional[Config] = None,
    ml_scorer: Optional[Any] = None,
) -> List[CausalRelation]:
    """识别事件两两之间的因果关系。

    Args:
        events: 事件列表（模块1产出或赛题提供）。
        config: 可选配置对象，覆盖 relation.* 下的阈值与开关。
        ml_scorer: 可选 ML 打分器（如 BertCausalScorer）。传入时用 ML 覆盖
                   规则的置信度与关系类型；为 None 时纯规则基线。

    Returns:
        CausalRelation 列表，每条为一条有向因果边。
    """
    if not events:
        log.debug("输入事件为空，返回空列表")
        return []

    log.info("开始因果关系抽取，输入事件 %d 个", len(events))

    # ML 批量模式：有 score_batch 接口时走批量路径，大幅加速 GPU 推理
    if ml_scorer is not None and hasattr(ml_scorer, "score_batch"):
        log.info("使用 ML 批量打分模式")
        relations = _extract_ml_batch(events, config, ml_scorer)
        log.info("因果关系抽取完成，共产出 %d 条关系", len(relations))
        return relations

    min_conf = float(_cfg(config, "min_confidence"))
    strict_temp = bool(_cfg(config, "strict_temporal"))

    # ---- 1. 按文档分组 ----
    by_doc: Dict[str, List[Event]] = {}
    for e in events:
        by_doc.setdefault(e.doc_id, []).append(e)

    relations: List[CausalRelation] = []
    seen_pairs: Set[Tuple[str, str]] = set()
    rid = 0

    for doc_id, doc_events in by_doc.items():
        log.debug("文档 %s：%d 个事件", doc_id, len(doc_events))

        # ---- 2. 按时间排序 ----
        sorted_events = sorted(doc_events, key=_sort_key)
        valid_ids = {e.event_id for e in sorted_events}
        n = len(sorted_events)

        # ---- 3. 两两配对 ----
        for i in range(n):
            for j in range(i + 1, n):
                e_a = sorted_events[i]   # 时间上较早
                e_b = sorted_events[j]   # 时间上较晚

                # 收集两个事件 mention 中命中的所有提示词
                hits_a = find_cues(e_a.mention)
                hits_b = find_cues(e_b.mention)

                # 根据提示词方向确定 cause/effect：
                #   forward  提示词所在事件是 effect，另一事件是 cause
                #   backward 提示词所在事件是 cause，另一事件是 effect
                candidates: List[Tuple[Event, Event, str, str, str, float]] = []
                for cue, rtype, direction, w in hits_a:
                    if direction == "backward":
                        candidates.append((e_a, e_b, cue, rtype, direction, w))  # e_a=因, e_b=果
                    else:  # forward: e_a 是果，e_b 是因（时序可能违例）
                        candidates.append((e_b, e_a, cue, rtype, direction, w))
                for cue, rtype, direction, w in hits_b:
                    if direction == "forward":
                        candidates.append((e_a, e_b, cue, rtype, direction, w))  # e_a=因, e_b=果
                    else:  # backward: e_b 是因，e_a 是果（时序可能违例）
                        candidates.append((e_b, e_a, cue, rtype, direction, w))

                if not candidates:
                    # ML 模式下不受提示词限制：对所有事件对打分
                    if ml_scorer is None:
                        continue
                    # 邻近性约束：无提示词时，只打分文本距离较近的事件对
                    dist = _char_distance(e_a, e_b)
                    prox_threshold = float(_cfg(config, "ml_proximity_threshold"))
                    if dist is not None and dist > prox_threshold:
                        continue
                    cause_evt, effect_evt = e_a, e_b  # 时间早的暂定为因，方向由双向打分决定
                    cue_word, rtype, direction, weight = "", "causal", "forward", 0.0
                    second_weight = 0.0
                else:
                    # 按时序一致性分组：cause.time <= effect.time 为一致
                    consistent = [
                        c for c in candidates
                        if not (c[0].time and c[1].time and c[0].time > c[1].time)
                    ]
                    # 有一致候选时只从一致中选；否则用不一致候选（受 strict_temporal 约束）
                    pool = consistent if consistent else candidates

                    # 按权重排序，取最优和次优（用于边际分差）
                    pool_sorted = sorted(pool, key=lambda c: c[5], reverse=True)
                    best = pool_sorted[0]
                    second_weight = pool_sorted[1][5] if len(pool_sorted) > 1 else 0.0
                    cause_evt, effect_evt, cue_word, rtype, direction, weight = best

                # ---- 4. 时序校验 ----
                temporal_ok = True
                if cause_evt.time and effect_evt.time and cause_evt.time > effect_evt.time:
                    if strict_temp:
                        log.debug(
                            "严格时序丢弃：%s(%s) -> %s(%s)",
                            cause_evt.event_id, cause_evt.time,
                            effect_evt.event_id, effect_evt.time,
                        )
                        continue
                    temporal_ok = False

                # ---- 5. 综合打分 ----
                if ml_scorer is not None:
                    # ML 模式：用模型打分，覆盖规则置信度与类型
                    has_cue = bool(cue_word)
                    if has_cue:
                        # 有提示词：方向由提示词决定，直接打分
                        ml_prob, ml_type = ml_scorer.score(cause_evt.mention, effect_evt.mention)
                    else:
                        # 无提示词：双向打分确定方向
                        prob_fwd, _ = ml_scorer.score(e_a.mention, e_b.mention)
                        prob_bwd, _ = ml_scorer.score(e_b.mention, e_a.mention)
                        direction_margin = float(_cfg(config, "ml_direction_margin"))
                        # 两个方向概率都不高 → 非因果
                        if prob_fwd < min_conf and prob_bwd < min_conf:
                            continue
                        # 两方向概率差太小 → 方向不确定，丢弃
                        if abs(prob_fwd - prob_bwd) < direction_margin:
                            log.debug(
                                "方向不确定：%s<->%s (fwd=%.3f, bwd=%.3f)",
                                e_a.event_id, e_b.event_id, prob_fwd, prob_bwd,
                            )
                            continue
                        # 取概率高的方向
                        if prob_fwd >= prob_bwd:
                            cause_evt, effect_evt = e_a, e_b
                            ml_prob, ml_type = prob_fwd, "causal"
                        else:
                            cause_evt, effect_evt = e_b, e_a
                            ml_prob, ml_type = prob_bwd, "causal"

                    if ml_type == "none" or ml_prob < min_conf:
                        log.debug(
                            "ML 判定无因果：%s -> %s (prob=%.3f, type=%s)",
                            cause_evt.event_id, effect_evt.event_id, ml_prob, ml_type,
                        )
                        continue
                    confidence = round(min(1.0, max(0.0, ml_prob)), 4)
                    rtype = ml_type
                    log.debug(
                        "ML 打分：%s -> %s conf=%.3f type=%s",
                        cause_evt.event_id, effect_evt.event_id, confidence, rtype,
                    )
                else:
                    # 规则基线模式
                    confidence = _score_pair(cause_evt, effect_evt, cue_word, weight, config)
                    if not temporal_ok:
                        confidence = max(0.3, confidence - 0.2)

                    # ---- 5b. 边际分差惩罚：最优与次优权重接近时降权 ----
                    margin = weight - second_weight
                    margin_threshold = float(_cfg(config, "margin_threshold"))
                    if margin < margin_threshold and second_weight > 0:
                        penalty = (margin_threshold - margin) / margin_threshold * 0.15
                        confidence = max(0.3, confidence - penalty)
                        log.debug(
                            "边际分差小(%.3f<%.3f)，降权 %.3f -> %.3f",
                            margin, margin_threshold, penalty, confidence,
                        )

                    # ---- 5c. 事件置信度因子：软化处理，避免低权重关系被压垮 ----
                    # 因子 = 0.5 + 0.5 × 平均事件置信度，范围 [0.5, 1.0]
                    evt_conf = (cause_evt.confidence + effect_evt.confidence) / 2.0
                    evt_factor = 0.5 + 0.5 * evt_conf
                    confidence *= evt_factor

                if confidence < min_conf:
                    log.debug(
                        "低于阈值 %.2f：%s -> %s conf=%.2f",
                        min_conf, cause_evt.event_id, effect_evt.event_id, confidence,
                    )
                    continue

                # ---- 6. 去重 ----
                pair = (cause_evt.event_id, effect_evt.event_id)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                rid += 1
                relations.append(
                    CausalRelation(
                        relation_id=f"R{rid:03d}",
                        cause_event_id=cause_evt.event_id,
                        effect_event_id=effect_evt.event_id,
                        relation_type=rtype,
                        evidence=_build_evidence(cause_evt, effect_evt),
                        confidence=round(confidence, 2),
                    )
                )
                log.debug(
                    "产出 %s: %s -> %s [%s] conf=%.2f (cue='%s')",
                    f"R{rid:03d}", cause_evt.event_id, effect_evt.event_id,
                    rtype, confidence, cue_word,
                )

    log.info("因果关系抽取完成，共产出 %d 条关系", len(relations))
    return relations
