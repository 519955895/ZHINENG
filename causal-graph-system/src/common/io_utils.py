"""公共 IO：目录创建、读写封装。"""
from __future__ import annotations

import os
from typing import List

from .schemas import (
    CausalGraph,
    CausalRelation,
    Document,
    Event,
    read_json,
    read_jsonl,
    write_json,
    write_jsonl,
)


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def load_documents(path: str) -> List[Document]:
    """读取原始文档（支持 JSON 数组或 JSONL）。"""
    if path.endswith(".jsonl"):
        return read_jsonl(path, Document)
    with open(path, "r", encoding="utf-8") as f:
        import json
        data = json.load(f)
    return [Document.from_dict(d) for d in data]


def save_events(events: List[Event], path: str) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    write_jsonl(path, events)


def load_events(path: str) -> List[Event]:
    return read_jsonl(path, Event)


def save_relations(relations: List[CausalRelation], path: str) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    write_jsonl(path, relations)


def load_relations(path: str) -> List[CausalRelation]:
    return read_jsonl(path, CausalRelation)


def save_graph(graph: CausalGraph, path: str) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    write_json(path, graph)


def load_graph(path: str) -> CausalGraph:
    return read_json(path, CausalGraph)
