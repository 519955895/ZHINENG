"""模块1：新闻内容抽取（成员 A）。

对外唯一入口：extract_events(documents) -> List[Event]
实现请在本目录下的 event_extractor.py 中完成。
"""
from .event_extractor import extract_events

__all__ = ["extract_events"]
