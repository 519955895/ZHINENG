"""运行因果抽取并打印可读的因果对（含事件文本）。"""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '.vendor')

from src.common.io_utils import load_events, save_relations
from src.relation.causal_relation import extract_relations
from src.relation.ml_scorer import create_ml_scorer

# 1. 加载事件
events = load_events("data/cec/cec_events.jsonl")
print(f"加载 {len(events)} 个事件\n")

# 建一个 event_id -> mention 的查找表
evt_map = {e.event_id: e for e in events}

# 2. 加载 ML 模型
scorer = create_ml_scorer("data/models/cec_causal_scorer")
print(f"ML 可用: {scorer is not None}\n")

# 3. 抽取因果关系（阈值 0.60 平衡精确率）
from src.common.config import Config
cfg = Config({"relation": {"min_confidence": 0.60}})
relations = extract_relations(events, config=cfg, ml_scorer=scorer)
print(f"产出 {len(relations)} 条因果关系\n")

# 4. 保存到文件
save_relations(relations, "data/output/cec_relations.jsonl")
print("结果已保存到: data/output/cec_relations.jsonl\n")

# 5. 打印前 20 条，显示事件文本
print("=" * 80)
print(f"{'#':>3} | {'置信度':>6} | 因 -> 果")
print("=" * 80)
for i, r in enumerate(relations[:20], 1):
    cause = evt_map.get(r.cause_event_id)
    effect = evt_map.get(r.effect_event_id)
    cause_text = cause.mention if cause else "(未知)"
    effect_text = effect.mention if effect else "(未知)"
    print(f"{i:>3} | {r.confidence:.3f} | {cause_text}  ->  {effect_text}")
