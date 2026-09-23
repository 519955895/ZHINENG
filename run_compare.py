"""对比 sklearn 与 BERT 模型的因果抽取效果。"""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '.vendor')

from src.common.io_utils import load_events
from src.relation.causal_relation import extract_relations
from src.relation.ml_scorer import create_ml_scorer

events = load_events("data/cec/cec_events.jsonl")
evt_map = {e.event_id: e for e in events}

from src.common.config import Config
cfg = Config({"relation": {"min_confidence": 0.60}})

def show(name, model_dir):
    scorer = create_ml_scorer(model_dir)
    rels = extract_relations(events, config=cfg, ml_scorer=scorer)
    print(f"\n{'='*80}")
    print(f"模型: {name}")
    print(f"产出: {len(rels)} 条因果关系")
    print(f"{'='*80}")
    print(f"{'#':>3} | {'置信度':>6} | 因 -> 果")
    print("-"*80)
    for i, r in enumerate(rels[:15], 1):
        c = evt_map.get(r.cause_event_id)
        e = evt_map.get(r.effect_event_id)
        ct = c.mention if c else "?"
        et = e.mention if e else "?"
        print(f"{i:>3} | {r.confidence:.3f} | {ct}  ->  {et}")

show("sklearn (TF-IDF+LR)", "data/models/cec_causal_scorer")
show("BERT (bert-base-chinese)", "data/models/cec_causal_scorer_bert")
