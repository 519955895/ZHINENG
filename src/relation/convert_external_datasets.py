"""将外部数据集转换为统一的 {cause, effect, label} JSONL 格式。

支持的数据源：
  1. CausalEventPairsDataset: cause@effect<TAB>freq  → 100k+ 对
  2. C-CSB: label(-3~3), sen(含因果连接词的完整句) → 6722 条

NTU Chinese Causal Corpus 只有元数据无原文，跳过。

输出格式（每行一条 JSON）：
  {"cause": "原因文本", "effect": "结果文本", "label": 1, "source": "causal_pairs"}
  {"cause": "句子的前半", "effect": "句子的后半", "label": 0, "source": "csb"}
"""
from __future__ import annotations

import csv
import json
import os
import re
from typing import List, Dict

# C-CSB 中的因果连接词列表（用于拆分句子）
CAUSE_CONNECTIVES = [
    "导致", "引起", "造成", "引发", "使得", "使", "以致", "以至",
    "故而", "是以", "因此", "令", "从而", "进而",
    "因为", "由于", "因", "源于",
]

EFFECT_CONNECTIVES = [
    "所以", "因此", "故", "因而", "从而", "以至于",
]


def convert_causal_event_pairs(filepath: str) -> List[Dict]:
    """转换 CausalEventPairsDataset。

    格式: cause@effect\tfreq
    过滤: 去掉长度过短（<2字）或过场（>100字）的文本，去掉频次<2的噪声。
    """
    results = []
    skipped = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 拆分 cause@effect 和 freq
            parts = line.rsplit("\t", 1)
            pair_str = parts[0]
            freq = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1

            # 频次太低的可能是噪声
            if freq < 2:
                skipped += 1
                continue

            # 拆分 cause@effect
            if "@" not in pair_str:
                skipped += 1
                continue
            cause, effect = pair_str.split("@", 1)
            cause = cause.strip()
            effect = effect.strip()

            # 过滤过短或过长
            if len(cause) < 2 or len(effect) < 2:
                skipped += 1
                continue
            if len(cause) > 100 or len(effect) > 100:
                skipped += 1
                continue

            results.append({
                "cause": cause,
                "effect": effect,
                "label": 1,
                "source": "causal_pairs",
                "freq": freq,
            })

    print(f"  CausalEventPairs: {len(results)} 条有效, 跳过 {skipped} 条噪声")
    return results


def convert_csb(filepath: str) -> List[Dict]:
    """转换 C-CSB。

    格式: CSV with columns [label, sen]
    label: -3(强非因果) ~ +3(强因果), 0=无因果
    sen: 完整句子，含因果连接词

    策略:
      - label > 0 → 正例（因果），用连接词拆分 cause/effect
      - label <= 0 → 负例（非因果），拆分成两半作为 cause/effect（标签0）
    """
    results = []
    split_success = 0
    split_fail = 0

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = int(row["label"])
            sen = row["sen"].strip()
            if not sen or len(sen) < 5:
                continue

            if label > 0:
                # 正例：尝试用连接词拆分
                cause, effect = _split_by_connective(sen)
                if cause and effect:
                    results.append({
                        "cause": cause,
                        "effect": effect,
                        "label": 1,
                        "source": "csb",
                        "strength": label,
                    })
                    split_success += 1
                else:
                    # 拆分失败，用整个句子作为 cause，空 effect
                    split_fail += 1
            else:
                # 负例：随机拆分成两半
                mid = len(sen) // 2
                # 尽量在逗号或句号处拆分
                split_pos = _find_split_point(sen, mid)
                results.append({
                    "cause": sen[:split_pos].strip("，。；"),
                    "effect": sen[split_pos:].strip("，。；"),
                    "label": 0,
                    "source": "csb",
                    "strength": label,
                })
                split_success += 1

    print(f"  C-CSB: {len(results)} 条 ({split_success} 拆分成功, {split_fail} 正例拆分失败)")
    return results


def _split_by_connective(sentence: str) -> tuple:
    """用因果连接词拆分句子为 (cause, effect)。

    前因后果型: "A导致B" → ("A", "B")
    前果后因型: "A因为B" → ("B", "A")
    """
    # 前因后果：连接词前面是因，后面是果
    for conn in CAUSE_CONNECTIVES:
        if conn in sentence:
            idx = sentence.find(conn)
            cause = sentence[:idx].strip("，。；！？ ")
            effect = sentence[idx + len(conn):].strip("，。；！？ 了")
            if len(cause) >= 2 and len(effect) >= 2:
                return (cause, effect)

    # 前果后因：连接词前面是果，后面是因
    for conn in EFFECT_CONNECTIVES:
        if conn in sentence:
            idx = sentence.find(conn)
            effect = sentence[:idx].strip("，。；！？ ")
            cause = sentence[idx + len(conn):].strip("，。；！？ ")
            if len(cause) >= 2 and len(effect) >= 2:
                return (cause, effect)

    return (None, None)


def _find_split_point(text: str, approx_pos: int) -> int:
    """在 approx_pos 附近找最近的标点符号作为拆分点。"""
    punctuation = "，。；！？、"
    # 向后找
    for i in range(approx_pos, min(len(text), approx_pos + 20)):
        if text[i] in punctuation:
            return i + 1
    # 向前找
    for i in range(approx_pos - 1, max(0, approx_pos - 20), -1):
        if text[i] in punctuation:
            return i + 1
    return approx_pos


def generate_negatives_from_causal_pairs(
    pairs: List[Dict], ratio: float = 0.5
) -> List[Dict]:
    """从正例中生成负例（交换 cause/effect 或随机配对）。

    策略：
      1. 交换 cause/effect → label=0（反向通常非因果）
      2. 随机配对不同正例的 cause 和 effect → label=0
    """
    import random
    random.seed(42)

    negatives = []

    # 策略1: 交换 cause/effect
    for p in pairs:
        if len(p["cause"]) >= 2 and len(p["effect"]) >= 2:
            negatives.append({
                "cause": p["effect"],
                "effect": p["cause"],
                "label": 0,
                "source": "causal_pairs_swapped",
            })

    # 策略2: 随机配对（控制数量）
    n_random = int(len(pairs) * ratio)
    indices = list(range(len(pairs)))
    random.shuffle(indices)
    for i in range(min(n_random, len(indices) - 1)):
        j = indices[i]
        k = indices[(i + 1) % len(indices)]
        if j != k:
            negatives.append({
                "cause": pairs[j]["cause"],
                "effect": pairs[k]["effect"],
                "label": 0,
                "source": "causal_pairs_random",
            })

    print(f"  负例生成: {len(negatives)} 条 (交换 {len(pairs)} + 随机 {min(n_random, len(indices)-1)})")
    return negatives


def merge_and_save(
    output_path: str = "data/training/merged_causal.jsonl",
):
    """合并所有数据集，生成统一训练文件。"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    all_data: List[Dict] = []

    # 1. CausalEventPairsDataset
    print("处理 CausalEventPairsDataset...")
    cep_path = "data/external/causal_event_pairs/CausalEventPairsDataset-main/causal.txt"
    if os.path.exists(cep_path):
        cep_pairs = convert_causal_event_pairs(cep_path)
        all_data.extend(cep_pairs)

        # 从正例生成负例
        negatives = generate_negatives_from_causal_pairs(cep_pairs)
        all_data.extend(negatives)
    else:
        print(f"  文件不存在: {cep_path}")

    # 2. C-CSB
    print("\n处理 C-CSB...")
    csb_path = "data/external/csb/CSB-dataset-main/C-CSB.csv"
    if os.path.exists(csb_path):
        csb_pairs = convert_csb(csb_path)
        all_data.extend(csb_pairs)
    else:
        print(f"  文件不存在: {csb_path}")

    # 3. CEC 已有标注（加上作为高质量正例）
    print("\n处理 CEC 标注数据...")
    cec_path = "data/cec/cec_gold_relations.jsonl"
    if os.path.exists(cec_path):
        cec_count = 0
        events_path = "data/cec/cec_events.jsonl"
        evt_map = {}
        if os.path.exists(events_path):
            with open(events_path, "r", encoding="utf-8") as f:
                for line in f:
                    evt = json.loads(line)
                    evt_map[evt["event_id"]] = evt.get("mention", "")

        with open(cec_path, "r", encoding="utf-8") as f:
            for line in f:
                rel = json.loads(line)
                cause_text = evt_map.get(rel.get("cause_event_id", ""), "")
                effect_text = evt_map.get(rel.get("effect_event_id", ""), "")
                if cause_text and effect_text:
                    all_data.append({
                        "cause": cause_text,
                        "effect": effect_text,
                        "label": 1,
                        "source": "cec_gold",
                    })
                    cec_count += 1
        print(f"  CEC: {cec_count} 条正例")
    else:
        print(f"  文件不存在: {cec_path}")

    # 统计
    pos = sum(1 for d in all_data if d["label"] == 1)
    neg = sum(1 for d in all_data if d["label"] == 0)
    sources = {}
    for d in all_data:
        sources[d["source"]] = sources.get(d["source"], 0) + 1

    print(f"\n{'='*50}")
    print(f"合并完成: 共 {len(all_data)} 条")
    print(f"  正例: {pos}")
    print(f"  负例: {neg}")
    print(f"  正负比: 1:{neg/max(pos,1):.2f}")
    print(f"\n各来源:")
    for src, cnt in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src}: {cnt}")

    # 保存
    with open(output_path, "w", encoding="utf-8") as f:
        for d in all_data:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"\n已保存到: {output_path}")
    return all_data


if __name__ == "__main__":
    merge_and_save()
