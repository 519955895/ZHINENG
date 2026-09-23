"""三方对比：规则基线 vs CEC-only BERT vs 合并数据集 BERT。

在 CEC 1407 事件 / 207 标注对上评估召回率/精确率/F1。
"""
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

# 加载 CEC 数据
events = load_events("data/cec/cec_events.jsonl")
evt_map = {e.event_id: e for e in events}

# 加载 gold relations
gold_pairs = set()
with open("data/cec/cec_gold_relations.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        gold_pairs.add((r["cause_event_id"], r["effect_event_id"]))

print(f"CEC: {len(events)} 个事件, {len(gold_pairs)} 条标注因果对\n")

cfg = Config({"relation": {"min_confidence": 0.60}})


def evaluate(name, model_dir=None, use_ml=False):
    """评估一个模型，输出召回率/精确率/F1。"""
    if use_ml and model_dir:
        scorer = create_ml_scorer(model_dir)
        if scorer is None:
            print(f"  [跳过] 模型加载失败: {model_dir}")
            return
        rels = extract_relations(events, config=cfg, ml_scorer=scorer)
    else:
        rels = extract_relations(events, config=cfg)

    n_output = len(rels)
    hits = 0
    for r in rels:
        if (r.cause_event_id, r.effect_event_id) in gold_pairs:
            hits += 1

    recall = hits / len(gold_pairs) if gold_pairs else 0
    precision = hits / n_output if n_output else 0
    f1 = 2 * recall * precision / (recall + precision) if (recall + precision) else 0

    print(f"{'='*60}")
    print(f"模型: {name}")
    print(f"  产出关系数: {n_output}")
    print(f"  命中数:     {hits}")
    print(f"  召回率:     {recall:.4f}")
    print(f"  精确率:     {precision:.4f}")
    print(f"  F1:         {f1:.4f}")
    print()

    # 输出前 10 条样例
    print(f"  前 10 条样例:")
    for i, r in enumerate(rels[:10], 1):
        c = evt_map.get(r.cause_event_id)
        e = evt_map.get(r.effect_event_id)
        ct = c.mention[:20] if c else "?"
        et = e.mention[:20] if e else "?"
        hit = "✓" if (r.cause_event_id, r.effect_event_id) in gold_pairs else " "
        print(f"    {i:>2}. [{hit}] {r.confidence:.3f} | {ct} -> {et}")
    print()
    return {"name": name, "n_output": n_output, "hits": hits,
            "recall": round(recall, 4), "precision": round(precision, 4), "f1": round(f1, 4)}


results = []

# A. 规则基线
print("评估 A: 规则基线...")
results.append(evaluate("A. 规则基线 (57 提示词)"))

# B. CEC-only BERT (207 对训练)
print("评估 B: CEC-only BERT...")
results.append(evaluate("B. CEC-only BERT (824样本)", "data/models/cec_causal_scorer_bert", use_ml=True))

# C. 合并数据集 BERT (28000 样本训练)
print("评估 C: 合并数据集 BERT...")
results.append(evaluate("C. 合并数据集 BERT (28000样本)", "data/models/merged_bert", use_ml=True))

# 汇总表
print(f"\n{'='*60}")
print(f"{'三方对比汇总':^60}")
print(f"{'='*60}")
print(f"{'模型':<35} {'产出':>5} {'命中':>4} {'召回率':>7} {'精确率':>7} {'F1':>7}")
print(f"{'-'*60}")
for r in results:
    print(f"{r['name']:<35} {r['n_output']:>5} {r['hits']:>4} {r['recall']:>7.4f} {r['precision']:>7.4f} {r['f1']:>7.4f}")
print(f"{'='*60}")
