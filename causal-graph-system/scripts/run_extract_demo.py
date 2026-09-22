# -*- coding: utf-8 -*-
"""把 data/raw/news.json 跑事件抽取，落盘 events.jsonl 并打印可读结果。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.io_utils import load_documents, save_events
from src.extraction.event_extractor import extract_events


def main() -> None:
    docs = load_documents(str(ROOT / "data" / "raw" / "news.json"))
    events = extract_events(docs)
    save_events(events, str(ROOT / "data" / "events" / "events.jsonl"))

    rows = []
    for e in events:
        rows.append({
            "event_id": e.event_id,
            "doc_id": e.doc_id,
            "event_type": e.event_type,
            "trigger": e.trigger,
            "mention": e.mention,
            "time": e.time,
            "location": e.location,
            "arguments": [{"role": a.role, "value": a.value} for a in e.arguments],
            "char_offset": list(e.char_offset) if e.char_offset else None,
            "confidence": e.confidence,
        })

    out = ROOT / "events_result.jsonl"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    print("TOTAL_EVENTS:", len(events))
    print("WROTE:", out)
    print("WROTE_EVENTS_JSONL:", ROOT / "data" / "events" / "events.jsonl")


if __name__ == "__main__":
    main()
