"""模块1 事件抽取精度评测（P / R / F1），对 DuEE 官方 dev/test 集。

背景：scripts/eval.py 评测的是模块3 QA 答案（answer_text 的 EM/F1），
      scripts/verify_extraction.py 只做契约自检（字段合法性），两者都不衡量
      模块1 抽取的"对不对"。本脚本补上这一环。

度量口径（业界标准，DuEE/ACE 通用，均为 micro P/R/F1）：
  1. 触发词识别 TI：触发词 span 完全一致（不看类型）。
  2. 触发词分类 TC：事件类型 + 触发词 span 同时一致。  ← 最常用主指标
  3. 论元识别 AI：论元文本完全一致（不看角色）。
  4. 论元分类 AC：角色 + 论元文本同时一致。

为什么不用 accuracy：事件抽取高度稀疏，一句话里绝大多数 span 都不是触发词/论元，
正负样本比可达 1:100 以上。accuracy 会因"什么都不抽"而虚高，毫无区分度。

黄金标注：DuEE 官方 duee_dev.json / duee_test.json（含 trigger_start_index、
argument_start_index 字符偏移）。gold 通过 src/extraction/schema_mapping.py
映射到团队 4 类 / 7 通用角色；预测在同一批 text 上用 extract_events 跑出，
再按文档对齐比较。

用法：
    python scripts/eval_extraction.py --gold data/raw/DuEE/duee_dev.json --model rule
    python scripts/eval_extraction.py --gold data/raw/DuEE/duee_test.json --model pai \\
        --model-path models/extraction/best.pt --device cuda

已知限制（当前契约所致，非评测 bug）：
  - Event 契约没有 trigger 偏移字段，预测触发词 span 由 char_offset + mention.find
    反推；Argument 契约只有 role/value、无偏移，故论元按"文本精确匹配"而非 span。
  - 规则基线的 time/location 会被归一化（如 "9月6日" -> "2026-09-06"），与原文
    不一致，论元 F1 会偏低——这是基线预期。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from src.common.schemas import Document  # noqa: E402
from src.extraction.event_extractor import extract_events  # noqa: E402
from src.extraction.schema_mapping import map_event_type, map_role  # noqa: E402


def _load_gold(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    if raw.startswith("["):
        return json.loads(raw)
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def _gold_records(rows: List[Dict[str, Any]]) -> List[Tuple]:
    """gold 事件 -> (doc_id, mapped_type, trigger_span, [(mapped_role, text), ...])"""
    recs: List[Tuple] = []
    for row in rows:
        doc_id = str(row.get("id", ""))
        for e in row.get("event_list") or []:
            mtype = map_event_type(e.get("event_type", ""))
            trig_text = (e.get("trigger") or "").strip()
            tstart = e.get("trigger_start_index")
            if not trig_text or not isinstance(tstart, int) or tstart < 0:
                continue
            args = []
            for a in e.get("arguments") or []:
                atext = (a.get("argument") or "").strip()
                if atext:
                    args.append((map_role(a.get("role", "")), atext))
            recs.append((doc_id, mtype, (tstart, tstart + len(trig_text)), args))
    return recs


def _pred_records(docs: List[Document], events) -> List[Tuple]:
    """预测事件 -> (doc_id, type, trigger_span, [(role, value), ...])"""
    text_map = {d.doc_id: d.text for d in docs}
    recs: List[Tuple] = []
    for ev in events:
        text = text_map.get(ev.doc_id, "")
        base = ev.char_offset[0] if ev.char_offset else 0
        idx = (ev.mention or "").find(ev.trigger)
        if idx == -1:  # 触发词不在 mention 内（异常），退而求全文定位
            idx = text.find(ev.trigger)
            base = 0
        if idx == -1:
            continue
        trig_span = (base + idx, base + idx + len(ev.trigger))
        recs.append((ev.doc_id, ev.event_type, trig_span,
                     [(a.role, a.value) for a in ev.arguments]))
    return recs


def _match(gold: Counter, pred: Counter) -> Tuple[int, int, int]:
    tp = sum((gold & pred).values())
    fp = sum(pred.values()) - tp
    fn = sum(gold.values()) - tp
    return tp, fp, fn


def _f1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return round(p, 4), round(r, 4), round(f, 4)


def main() -> None:
    p = argparse.ArgumentParser(description="模块1 事件抽取精度评测")
    p.add_argument("--gold", required=True, help="DuEE 官方 duee_dev/duee_test.json")
    p.add_argument("--model", default="rule", help="rule / pai")
    p.add_argument("--model-path", default="", help="pai 权重路径（相对项目根）")
    p.add_argument("--threshold", type=float, default=0.5, help="pai 类型概率阈值")
    p.add_argument("--device", default="auto", help="auto / cpu / cuda")
    p.add_argument("--max-samples", type=int, default=0, help="调试：只取前 N 篇")
    args = p.parse_args()

    rows = _load_gold(args.gold)
    if args.max_samples > 0:
        rows = rows[: args.max_samples]

    gold = _gold_records(rows)
    docs = [Document(doc_id=str(r.get("id", "")), title="", text=r.get("text", ""))
            for r in rows]

    cfg = {"model": args.model, "threshold": args.threshold, "device": args.device}
    if args.model_path:
        cfg["model_path"] = args.model_path
    events = extract_events(docs, extraction_config=cfg)
    pred = _pred_records(docs, events)

    g_ti = Counter((d, s) for d, t, s, a in gold)
    g_tc = Counter((d, t, s) for d, t, s, a in gold)
    g_ai = Counter((d, v) for d, t, s, a in gold for r, v in a)
    g_ac = Counter((d, r, v) for d, t, s, a in gold for r, v in a)

    p_ti = Counter((d, s) for d, t, s, a in pred)
    p_tc = Counter((d, t, s) for d, t, s, a in pred)
    p_ai = Counter((d, v) for d, t, s, a in pred for r, v in a)
    p_ac = Counter((d, r, v) for d, t, s, a in pred for r, v in a)

    ti = _f1(*_match(g_ti, p_ti))
    tc = _f1(*_match(g_tc, p_tc))
    ai = _f1(*_match(g_ai, p_ai))
    ac = _f1(*_match(g_ac, p_ac))

    print("=" * 60)
    print("模块1 事件抽取评测（micro P / R / F1）")
    print(f"数据集：{args.gold}")
    print(f"文档 {len(rows)} 篇 | 黄金事件 {len(gold)} 个 | 预测事件 {len(pred)} 个")
    print("-" * 60)
    print(f"触发词识别 TI（span）           P={ti[0]:.4f}  R={ti[1]:.4f}  F1={ti[2]:.4f}")
    print(f"触发词分类 TC（type+span）★     P={tc[0]:.4f}  R={tc[1]:.4f}  F1={tc[2]:.4f}")
    print(f"论元识别 AI（文本）             P={ai[0]:.4f}  R={ai[1]:.4f}  F1={ai[2]:.4f}")
    print(f"论元分类 AC（role+文本）        P={ac[0]:.4f}  R={ac[1]:.4f}  F1={ac[2]:.4f}")

    print("-" * 60)
    print("各事件类型触发词分类（TC）诊断：")
    for t in sorted({e[1] for e in gold} | {e[1] for e in pred}):
        g = Counter((d, tt, s) for d, tt, s, a in gold if tt == t)
        pp = Counter((d, tt, s) for d, tt, s, a in pred if tt == t)
        _, _, f = _f1(*_match(g, pp))
        print(f"  {t:<8} F1={f:.4f}  (gold={sum(g.values())}, pred={sum(pp.values())})")
    print("=" * 60)


if __name__ == "__main__":
    main()
