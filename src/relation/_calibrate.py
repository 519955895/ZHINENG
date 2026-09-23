"""模块2 权重标定工具（开发期使用，非运行时依赖）。

解决两个遗留问题：
  1. 提示词权重无数据支撑 → 统计 P(causal|cue) 作为权重
  2. 特征权重无学习过程   → 基于正/负例的特征区分度学习各特征权重

用法：
    python -m src.relation._calibrate \\
        --events data/events/events_sample.jsonl \\
        --gold-relations data/relations/gold_relations.jsonl \\
        --output-dir data/weights/

注意：--gold-relations 应为人工标注的真实因果对。
      若用模块2自产出的 relations，标定结果会偏向规则自身（仅用于演示流程）。
"""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from ..common.io_utils import load_events, load_relations
from ..common.schemas import CausalRelation, Event
from ..common.logger import get_logger
from .cue_pattern import CAUSAL_CUES, find_cues
from .causal_relation import _char_distance, _shared_args

log = get_logger("relation.calibrate")

# 可选依赖检测
try:
    import numpy as np
    from sklearn.linear_model import LogisticRegression

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


# ---------- 特征提取 ----------

def _extract_features(
    cause: Event, effect: Event, cue_weight: float
) -> Dict[str, float]:
    """提取一对事件的特征向量。"""
    # 位置邻近性（归一化到 [0,1]，越大越近）
    dist = _char_distance(cause, effect)
    location = max(0.0, 1.0 - dist / 500.0) if dist is not None else 0.0

    # 论元重叠（归一化到 [0,1]）
    shared = _shared_args(cause, effect)
    argument = min(1.0, len(shared) / 2.0)

    # 时间接近（前缀匹配长度 / 10）
    time_match = 0.0
    if cause.time and effect.time:
        common = 0
        for ca, cb in zip(cause.time, effect.time):
            if ca == cb:
                common += 1
            else:
                break
        time_match = min(1.0, common / 10.0)

    return {
        "cue_weight": cue_weight,
        "location": location,
        "argument": argument,
        "time_match": time_match,
    }


# ---------- 提示词权重标定 ----------

def calibrate_cue_weights(
    events: List[Event], gold_relations: List[CausalRelation]
) -> Dict[str, float]:
    """统计每个提示词的精确率 P(causal|cue) 作为权重。

    对每条标注因果对 (cause, effect)，扫描双方 mention 中的提示词，
    该提示词"断言"了因果关系。统计：
      - count[cue]   : 该提示词作为因果断言出现的次数
      - hit[cue]     : 其中真实为因果的次数
    精确率 = (hit + α) / (count + 2α) （拉普拉斯平滑，α=1）
    """
    gold_pairs = {(r.cause_event_id, r.effect_event_id) for r in gold_relations}
    evt_map = {e.event_id: e for e in events}

    count: Dict[str, int] = defaultdict(int)
    hit: Dict[str, int] = defaultdict(int)
    alpha = 1.0  # 拉普拉斯平滑

    # 遍历所有事件对，看哪些提示词"断言"了因果
    for i, e_a in enumerate(events):
        for e_b in events[i + 1:]:
            if e_a.doc_id != e_b.doc_id:
                continue
            # 扫描两个事件 mention 中的提示词
            for cue, rtype, direction, _ in find_cues(e_a.mention) + find_cues(e_b.mention):
                count[cue] += 1
                # 判断该提示词断言的方向是否对应真实因果对
                # 简化：只要 (e_a, e_b) 或 (e_b, e_a) 在 gold 中即算命中
                if (e_a.event_id, e_b.event_id) in gold_pairs or \
                   (e_b.event_id, e_a.event_id) in gold_pairs:
                    hit[cue] += 1

    weights: Dict[str, float] = {}
    for cue, rtype, direction, _ in CAUSAL_CUES:
        c = count.get(cue, 0)
        h = hit.get(cue, 0)
        precision = (h + alpha) / (c + 2 * alpha)
        weights[cue] = round(precision, 4)

    return weights


# ---------- 特征权重学习 ----------

FEATURE_NAMES = ["cue_weight", "location", "argument", "time_match"]


def _collect_feature_matrix(
    events: List[Event], gold_relations: List[CausalRelation]
) -> Tuple[List[List[float]], List[int]]:
    """收集所有候选对的特征矩阵 X 和标签 y。

    Returns:
        (X, y): X 为特征向量列表，y 为 0/1 标签（1=真实因果对）
    """
    gold_pairs = {(r.cause_event_id, r.effect_event_id) for r in gold_relations}
    X: List[List[float]] = []
    y: List[int] = []

    for i, e_a in enumerate(events):
        for e_b in events[i + 1:]:
            if e_a.doc_id != e_b.doc_id:
                continue
            all_cues = find_cues(e_a.mention) + find_cues(e_b.mention)
            if not all_cues:
                continue
            best_cue_weight = max(c[3] for c in all_cues)
            feats = _extract_features(e_a, e_b, best_cue_weight)
            X.append([feats[f] for f in FEATURE_NAMES])
            is_pos = (e_a.event_id, e_b.event_id) in gold_pairs or \
                     (e_b.event_id, e_a.event_id) in gold_pairs
            y.append(1 if is_pos else 0)

    return X, y


def _normalize_weights(raw: Dict[str, float]) -> Dict[str, float]:
    """归一化权重（和为1），保证 cue_weight 占比 ≥ 50%。"""
    epsilon = 1e-6
    total = sum(raw.values())
    if total < epsilon:
        return {"cue_weight": 0.5, "location": 0.2, "argument": 0.2, "time_match": 0.1}

    normalized = {f: w / total for f, w in raw.items()}
    if normalized["cue_weight"] < 0.5:
        deficit = 0.5 - normalized["cue_weight"]
        normalized["cue_weight"] = 0.5
        others = [f for f in FEATURE_NAMES if f != "cue_weight"]
        other_sum = sum(normalized[f] for f in others)
        for f in others:
            normalized[f] = max(0.0, normalized[f] - deficit * (normalized[f] / other_sum))

    return {f: round(w, 4) for f, w in normalized.items()}


def _weights_by_discriminability(X: List[List[float]], y: List[int]) -> Dict[str, float]:
    """纯 Python：基于正/负例特征区分度计算权重。"""
    epsilon = 1e-6
    pos_vals: Dict[str, List[float]] = {f: [] for f in FEATURE_NAMES}
    neg_vals: Dict[str, List[float]] = {f: [] for f in FEATURE_NAMES}

    for row, label in zip(X, y):
        target = pos_vals if label == 1 else neg_vals
        for f, val in zip(FEATURE_NAMES, row):
            target[f].append(val)

    raw: Dict[str, float] = {}
    for f in FEATURE_NAMES:
        pos = pos_vals[f]
        neg = neg_vals[f]
        if not pos or not neg:
            raw[f] = 0.0
            continue
        mu_pos = sum(pos) / len(pos)
        mu_neg = sum(neg) / len(neg)
        std_pos = (sum((x - mu_pos) ** 2 for x in pos) / len(pos)) ** 0.5
        std_neg = (sum((x - mu_neg) ** 2 for x in neg) / len(neg)) ** 0.5
        raw[f] = abs(mu_pos - mu_neg) / (std_pos + std_neg + epsilon)

    return _normalize_weights(raw)


def _weights_by_logistic_regression(X: List[List[float]], y: List[int]) -> Dict[str, float]:
    """sklearn：用逻辑回归系数绝对值作为特征权重。"""
    X_arr = np.array(X)
    y_arr = np.array(y)
    # 正负例都有时才训练
    if len(set(y)) < 2:
        log.warning("标签只有单一类别，回退到区分度方法")
        return _weights_by_discriminability(X, y)

    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_arr, y_arr)
    coefs = np.abs(clf.coef_[0])
    raw = {f: float(c) for f, c in zip(FEATURE_NAMES, coefs)}
    log.info("逻辑回归训练完成，系数: %s", {f: round(raw[f], 4) for f in FEATURE_NAMES})
    return _normalize_weights(raw)


def learn_feature_weights(
    events: List[Event], gold_relations: List[CausalRelation]
) -> Dict[str, float]:
    """学习各特征权重。

    - sklearn 可用且样本 ≥ 10 时：用逻辑回归系数绝对值（更可靠）
    - 否则：用正/负例特征区分度（纯 Python，无依赖）
    """
    X, y = _collect_feature_matrix(events, gold_relations)
    if not X:
        return {"cue_weight": 0.5, "location": 0.2, "argument": 0.2, "time_match": 0.1}

    n_pos = sum(y)
    log.info("特征学习：%d 个样本（正例 %d，负例 %d）", len(X), n_pos, len(X) - n_pos)

    if _SKLEARN_AVAILABLE and len(X) >= 10:
        log.info("使用 sklearn LogisticRegression 学习特征权重")
        return _weights_by_logistic_regression(X, y)
    else:
        if not _SKLEARN_AVAILABLE:
            log.info("sklearn 不可用，使用区分度方法学习特征权重")
        else:
            log.info("样本量不足(%d<10)，使用区分度方法学习特征权重", len(X))
        return _weights_by_discriminability(X, y)


# ---------- 主流程 ----------

def main():
    parser = argparse.ArgumentParser(description="模块2 权重标定工具")
    parser.add_argument("--events", required=True, help="事件 JSONL 路径")
    parser.add_argument("--gold-relations", required=True, help="人工标注因果对 JSONL 路径")
    parser.add_argument("--output-dir", default="data/weights", help="权重输出目录")
    args = parser.parse_args()

    events = load_events(args.events)
    gold_rels = load_relations(args.gold_relations)
    print(f"加载 {len(events)} 个事件，{len(gold_rels)} 条标注因果对")

    # 1. 标定提示词权重
    cue_weights = calibrate_cue_weights(events, gold_rels)
    print(f"\n=== 提示词权重标定结果（共 {len(cue_weights)} 个）===")
    for cue, w in sorted(cue_weights.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cue:6s}: {w:.4f}")

    # 2. 学习特征权重
    feat_weights = learn_feature_weights(events, gold_rels)
    print(f"\n=== 特征权重学习结果 ===")
    for f, w in feat_weights.items():
        print(f"  {f:12s}: {w:.4f}")

    # 3. 输出
    os.makedirs(args.output_dir, exist_ok=True)
    cue_path = os.path.join(args.output_dir, "cue_weights.json")
    feat_path = os.path.join(args.output_dir, "feature_weights.json")
    with open(cue_path, "w", encoding="utf-8") as f:
        json.dump(cue_weights, f, ensure_ascii=False, indent=2)
    with open(feat_path, "w", encoding="utf-8") as f:
        json.dump(feat_weights, f, ensure_ascii=False, indent=2)
    print(f"\n已输出：{cue_path}")
    print(f"已输出：{feat_path}")
    print("\n⚠️  若 --gold-relations 为模块2自产出数据，标定结果偏向规则自身。")
    print("    真实标定需用人工标注的因果对。")


if __name__ == "__main__":
    main()
