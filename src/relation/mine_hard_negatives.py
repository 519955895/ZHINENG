"""从 CEC 语料挖掘"硬负例"——同文档内语义相关但非因果的事件对。

这些负例比随机配对更难区分，能教模型识别"共现≠因果"，缓解域偏移。

策略：
  1. 按 doc_id 分组 CEC 事件
  2. 标注因果对（正向+反向）作为正例，排除
  3. 剩余同文档有序对中，筛选"硬"负例：
     - 共享关键词（伤亡/救援/灾害类词汇）
     - 时间邻近（同时间段）
     - 同事件类型
  4. 按难度打分排序，取前 N 条

用法：
    python -m src.relation.mine_hard_negatives \\
        --events data/cec/cec_events.jsonl \\
        --gold-relations data/cec/cec_gold_relations.jsonl \\
        --output data/training/cec_hard_negatives.jsonl \\
        --num-samples 800
"""
import argparse
import json
import random
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple


# 关键词类：同文档内同时出现这些词的事件对，语义相关但常非因果
CATEGORY_KEYWORDS = {
    "casualty": ["死亡", "受伤", "失踪", "遇难", "伤亡", "丧生", "受灾", "无家可归"],
    "rescue": ["救援", "援助", "救助", "直升机", "医疗队", "搜救", "慰问", "捐款"],
    "disaster": ["地震", "火灾", "爆炸", "事故", "洪水", "坍塌", "泄漏", "塌方", "泥石流"],
    "gov_action": ["调查", "处置", "处理", "部署", "采取", "启动", "发布", "通报"],
}


def load_jsonl(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def get_keywords(text: str) -> Set[str]:
    found = set()
    for words in CATEGORY_KEYWORDS.values():
        for w in words:
            if w in text:
                found.add(w)
    return found


def shared_keywords(t1: str, t2: str) -> Set[str]:
    return get_keywords(t1) & get_keywords(t2)


def time_similarity(t1: str, t2: str) -> bool:
    """两事件时间描述有交集即视为时间邻近。"""
    if not t1 or not t2:
        return False
    # 提取数字（日/月）
    n1 = set(re.findall(r"\d+", t1))
    n2 = set(re.findall(r"\d+", t2))
    if n1 & n2:
        return True
    # 直接包含
    return t1 in t2 or t2 in t1


def score_hardness(cause_text: str, effect_text: str, cause_time: str, effect_time: str) -> Tuple[int, str]:
    """给负例打分，越高越"难"（越像因果）。"""
    score = 0
    reasons = []

    sk = shared_keywords(cause_text, effect_text)
    if sk:
        score += len(sk) * 3
        reasons.append(f"共享关键词:{','.join(sk)}")

    if time_similarity(cause_time, effect_time):
        score += 2
        reasons.append("时间邻近")

    # 长度相近（事件级对）
    if 5 <= len(cause_text) <= 40 and 5 <= len(effect_text) <= 40:
        score += 1
        reasons.append("长度相当")

    # 触发词重叠（如都是"伤亡"类）
    if any(w in cause_text and w in effect_text for w in ["死亡", "受伤", "失踪"]):
        score += 3
        reasons.append("同属伤亡类")

    return score, ";".join(reasons)


def main():
    parser = argparse.ArgumentParser(description="挖掘 CEC 硬负例")
    parser.add_argument("--events", default="data/cec/cec_events.jsonl")
    parser.add_argument("--gold-relations", default="data/cec/cec_gold_relations.jsonl")
    parser.add_argument("--output", default="data/training/cec_hard_negatives.jsonl")
    parser.add_argument("--num-samples", type=int, default=800, help="最终产出的硬负例数量")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    events = load_jsonl(args.events)
    gold = load_jsonl(args.gold_relations)
    print(f"加载 {len(events)} 个事件, {len(gold)} 条标注因果对")

    # 按 doc_id 分组
    by_doc: Dict[str, List[dict]] = defaultdict(list)
    for e in events:
        by_doc[e["doc_id"]].append(e)

    # 标注因果对集合（正向+反向都排除）
    gold_pairs: Set[Tuple[str, str]] = set()
    for r in gold:
        gold_pairs.add((r["cause_event_id"], r["effect_event_id"]))

    # 挖所有非因果对并打分
    candidates = []
    for doc_id, doc_events in by_doc.items():
        n = len(doc_events)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                ei, ej = doc_events[i], doc_events[j]
                # 跳过标注因果
                if (ei["event_id"], ej["event_id"]) in gold_pairs:
                    continue
                score, reason = score_hardness(
                    ei["mention"], ej["mention"],
                    ei.get("time", ""), ej.get("time", "")
                )
                if score > 0:
                    candidates.append({
                        "cause": ei["mention"],
                        "effect": ej["mention"],
                        "label": 0,
                        "source": "cec_hard_negative",
                        "cause_event_id": ei["event_id"],
                        "effect_event_id": ej["event_id"],
                        "doc_id": doc_id,
                        "hardness_score": score,
                        "reason": reason,
                    })

    print(f"共挖取 {len(candidates)} 条带特征的非因果对")

    # 按难度降序，同难度打乱
    candidates.sort(key=lambda x: (-x["hardness_score"], random.random()))

    # 取前 num_samples
    selected = candidates[:args.num_samples]

    # 打印分布
    score_dist = defaultdict(int)
    for c in selected:
        score_dist[c["hardness_score"]] += 1
    print(f"难度分布: {dict(sorted(score_dist.items()))}")

    # 示例
    print(f"\n前 10 条最难负例:")
    for c in selected[:10]:
        print(f"  [难度{c['hardness_score']}] {c['cause'][:15]} -> {c['effect'][:15]}  ({c['reason']})")

    # 保存
    with open(args.output, "w", encoding="utf-8") as f:
        for c in selected:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"\n已保存 {len(selected)} 条硬负例到 {args.output}")


if __name__ == "__main__":
    main()
