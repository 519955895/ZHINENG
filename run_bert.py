"""BERT 因果抽取 - 运行并查看结果。"""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '.vendor')

from src.common.io_utils import load_events, save_relations
from src.relation.causal_relation import extract_relations
from src.relation.ml_scorer import create_ml_scorer
from src.common.config import Config

# 1. 加载事件
events = load_events("data/cec/cec_events.jsonl")
print(f"加载 {len(events)} 个事件\n")
evt_map = {e.event_id: e for e in events}

# 2. 加载 BERT 模型
scorer = create_ml_scorer("data/models/cec_causal_scorer_bert")
print(f"BERT 模型加载完成\n")

# 3. 抽取因果关系
cfg = Config({"relation": {"min_confidence": 0.60}})
relations = extract_relations(events, config=cfg, ml_scorer=scorer)
print(f"产出 {len(relations)} 条因果关系\n")

# 4. 保存到文件
save_relations(relations, "data/output/cec_bert_relations.jsonl")
print("结果已保存到: data/output/cec_bert_relations.jsonl\n")

# 5. 打印前 30 条
print("=" * 90)
print(f"{'#':>3} | {'置信度':>6} | {'类型':<8} | 因 -> 果")
print("=" * 90)
for i, r in enumerate(relations[:30], 1):
    cause = evt_map.get(r.cause_event_id)
    effect = evt_map.get(r.effect_event_id)
    ct = cause.mention if cause else "(未知)"
    et = effect.mention if effect else "(未知)"
    print(f"{i:>3} | {r.confidence:.3f} | {r.relation_type:<8} | {ct}  ->  {et}")

print(f"\n... 共 {len(relations)} 条，完整结果见 data/output/cec_bert_relations.jsonl")
