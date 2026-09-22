"""模块1 契约自检：用 sample 数据调用 extract_events 并校验契约约束。

用法：
    python scripts/verify_extraction.py

校验项（对应 docs/interface.md 与 docs/module1_extraction.md 的自查清单）：
- event_id 全局唯一；
- event_type ∈ 团队 4 类；
- Argument.role ∈ 通用角色表；
- mention 可被 char_offset 精确回溯（text[start:end] == mention）；
- confidence ∈ [0,1]。
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from src.common.io_utils import load_documents, load_events, save_events
from src.extraction.event_extractor import EVENT_TYPES, extract_events

GENERIC_ROLES = {"subject", "object", "time", "location", "instrument", "manner", "result"}
SAMPLE = os.path.join(_ROOT, "data", "raw", "news_sample.json")


def main() -> None:
    docs = load_documents(SAMPLE)
    text_map = {d.doc_id: d.text for d in docs}

    events = extract_events(docs)
    print(f"文档 {len(docs)} 篇 -> 事件 {len(events)} 个\n")

    ids = set()
    ok = True
    for e in events:
        text = text_map.get(e.doc_id, "")
        mention_ok = bool(e.char_offset) and \
            text[e.char_offset[0]:e.char_offset[1]] == e.mention
        conf_ok = 0.0 <= e.confidence <= 1.0
        type_ok = e.event_type in EVENT_TYPES
        role_ok = all(a.role in GENERIC_ROLES for a in e.arguments)
        id_ok = e.event_id not in ids
        ids.add(e.event_id)

        row_ok = all([mention_ok, conf_ok, type_ok, role_ok, id_ok])
        ok = ok and row_ok
        print(f"{e.event_id} | {e.event_type} | trigger={e.trigger} | mention={e.mention!r}")
        print(f"    time={e.time} location={e.location} offset={e.char_offset} "
              f"conf={e.confidence} args={[(a.role, a.value) for a in e.arguments]}")
        if not row_ok:
            print(f"    !! 校验失败 mention_ok={mention_ok} conf_ok={conf_ok} "
                  f"type_ok={type_ok} role_ok={role_ok} id_ok={id_ok}")

    # 编排器落盘链路：save_events -> load_events 回读一致
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "events.jsonl")
        save_events(events, out)
        back = load_events(out)
    roundtrip_ok = back == events
    ok = ok and roundtrip_ok
    print(f"落盘回读 roundtrip: {'通过' if roundtrip_ok else '失败'} ({len(back)} 个)")

    print(f"\n{'契约校验全部通过' if ok else '存在契约违规'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
