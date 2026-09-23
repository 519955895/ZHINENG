"""对合并数据集 BERT 做阈值扫描，找最佳平衡点。"""
import sys
import os
import json

sys.path.insert(0, '.')
sys.path.insert(0, '.vendor')

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from src.common.io_utils import load_events
from src.common.config import Config
from src.relation.causal_relation import extract_relations
from src.relation.ml_scorer import create_ml_scorer

events = load_events("data/cec/cec_events.jsonl")
evt_map = {e.event_id: e for e in events}

gold_pairs = set()
with open("data/cec/cec_gold_relations.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        gold_pairs.add((r["cause_event_id"], r["effect_event_id"]))

print(f"CEC: {len(events)} 个事件, {len(gold_pairs)} 条标注因果对\n")

# 先加载模型，跑一次批量打分拿到所有分数
scorer = create_ml_scorer("data/models/merged_bert")
print(f"模型已加载\n")

thresholds = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]

print(f"{'阈值':>6} | {'产出':>6} | {'命中':>4} | {'召回率':>7} | {'精确率':>7} | {'F1':>7}")
print("-" * 55)

best_f1 = 0
best_threshold = 0
results = []

for threshold in thresholds:
    cfg = Config({"relation": {"min_confidence": threshold}})
    rels = extract_relations(events, config=cfg, ml_scorer=scorer)

    n_output = len(rels)
    hits = sum(1 for r in rels if (r.cause_event_id, r.effect_event_id) in gold_pairs)
    recall = hits / len(gold_pairs) if gold_pairs else 0
    precision = hits / n_output if n_output else 0
    f1 = 2 * recall * precision / (recall + precision) if (recall + precision) else 0

    results.append({"threshold": threshold, "n_output": n_output, "hits": hits,
                    "recall": round(recall, 4), "precision": round(precision, 4), "f1": round(f1, 4)})

    print(f"{threshold:>6.2f} | {n_output:>6} | {hits:>4} | {recall:>7.4f} | {precision:>7.4f} | {f1:>7.4f}")

    if f1 > best_f1:
        best_f1 = f1
        best_threshold = threshold

print(f"\n最佳阈值: {best_threshold:.2f} (F1={best_f1:.4f})")

# 用最佳阈值输出样例
print(f"\n{'='*60}")
print(f"最佳阈值 {best_threshold:.2f} 的前 20 条样例:")
print(f"{'='*60}")
cfg = Config({"relation": {"min_confidence": best_threshold}})
rels = extract_relations(events, config=cfg, ml_scorer=scorer)
for i, r in enumerate(rels[:20], 1):
    c = evt_map.get(r.cause_event_id)
    e = evt_map.get(r.effect_event_id)
    ct = c.mention[:25] if c else "?"
    et = e.mention[:25] if e else "?"
    hit = "✓" if (r.cause_event_id, r.effect_event_id) in gold_pairs else " "
    print(f"  {i:>2}. [{hit}] {r.confidence:.3f} | {ct} -> {et}")
