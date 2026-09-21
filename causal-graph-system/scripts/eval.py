"""评测脚本：对比系统输出答案与标注答案。

用法：
    python scripts/eval.py --pred data/output/challenge/answers.json \
                           --gold data/output/gold.json
"""
from __future__ import annotations

import argparse
import json


def _exact_match(pred: str, gold: str) -> bool:
    return pred.strip() == gold.strip()


def _f1_overlap(pred_tokens, gold_tokens) -> float:
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = len(set(pred_tokens) & set(gold_tokens))
    p = common / len(set(pred_tokens))
    r = common / len(set(gold_tokens))
    return 2 * p * r / (p + r) if (p + r) else 0.0


def evaluate(pred_path: str, gold_path: str) -> dict:
    with open(pred_path, "r", encoding="utf-8") as f:
        preds = json.load(f)
    with open(gold_path, "r", encoding="utf-8") as f:
        golds = json.load(f)

    gold_map = {g["query_id"]: g for g in golds}
    em = ev = 0
    n = len(golds)
    for p in preds:
        g = gold_map.get(p["query_id"])
        if not g:
            continue
        if _exact_match(p.get("answer_text", ""), g.get("answer_text", "")):
            em += 1
        ev += _f1_overlap(
            p.get("answer_text", "").split(),
            g.get("answer_text", "").split(),
        )
    report = {
        "total": n,
        "exact_match": em,
        "EM": em / n if n else 0.0,
        "avg_F1": ev / n if n else 0.0,
    }
    return report


def main() -> None:
    p = argparse.ArgumentParser(description="评测系统输出")
    p.add_argument("--pred", required=True)
    p.add_argument("--gold", required=True)
    args = p.parse_args()
    report = evaluate(args.pred, args.gold)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
