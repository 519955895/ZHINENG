"""IO 工具测试：事件/关系/图谱落盘再读回。"""
import os
import tempfile

from src.common.io_utils import load_events, save_events
from src.common.schemas import Event


def test_event_jsonl_roundtrip():
    events = [
        Event(event_id="E001", doc_id="D001", event_type="t", trigger="x", mention="m1"),
        Event(event_id="E002", doc_id="D001", event_type="t", trigger="x", mention="m2"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "events.jsonl")
        save_events(events, path)
        loaded = load_events(path)
        assert loaded == events
