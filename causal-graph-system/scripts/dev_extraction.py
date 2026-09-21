"""成员 A 独立调试脚本：不依赖 B/C 的代码，单独验证事件抽取。

用法：py scripts/dev_extraction.py
说明：用 data/raw/news_sample.json 作输入，产出 data/events/events_dev.jsonl。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.io_utils import load_documents, save_events  # noqa: E402
from src.extraction import extract_events  # noqa: E402


def main() -> None:
    docs = load_documents("data/raw/news_sample.json")
    print(f"载入 {len(docs)} 篇文档")

    try:
        events = extract_events(docs)
    except NotImplementedError:
        print("[模块1 未实现] 请在 src/extraction/event_extractor.py 中实现 extract_events")
        return

    save_events(events, "data/events/events_dev.jsonl")
    print(f"抽取到 {len(events)} 个事件 -> data/events/events_dev.jsonl")
    for e in events[:10]:
        print(f"  {e.event_id} | {e.event_type} | {e.mention} | conf={e.confidence}")


if __name__ == "__main__":
    main()
