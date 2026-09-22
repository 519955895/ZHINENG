#!/usr/bin/env python
"""把 DuEE 1.0 官方数据转换为训练用 train_events.jsonl（成员 A · 模块1 训练数据）。

用法：
    # 1. 默认读取本地官方数据 data/raw/DuEE/duee_train.json（无需联网）
    python scripts/prepare_duee_data.py

    # 2. 指定输出路径
    python scripts/prepare_duee_data.py --output data/raw/train_events.jsonl

    # 3. 指定本地数据文件（官方 JSONL 格式）
    python scripts/prepare_duee_data.py --input data/raw/DuEE/duee_train.json

输出格式（train_events.jsonl，每行一个句子）：
{
  "text": "雀巢裁员4000人：时代抛弃你时，连招呼都不会打！",
  "events": [
    {
      "event_type": "组织关系-裁员",        // 原始 DuEE 类型（PAIE 训练槽位）
      "mapped_type": "经济/涨跌",           // 映射后的团队 4 类（推理后处理用）
      "trigger": {"start": 2, "end": 4, "text": "裁员"},
      "arguments": [
        {"role": "裁员方", "mapped_role": "subject", "start": 0, "end": 2, "text": "雀巢"},
        {"role": "裁员人数", "mapped_role": "object", "start": 4, "end": 9, "text": "4000人"}
      ]
    }
  ]
}

说明：
- start/end 为「半开区间」字符偏移，与 Event.char_offset 语义一致；
- event_type / role 保留 DuEE 原始值供 PAIE 训练，mapped_type / mapped_role 供后处理归一到契约；
- 默认丢弃无触发词的事件（a 方案需要 trigger 标注），可用 --keep-no-trigger 保留。

依赖：离线转换无需额外依赖；仅在线下载需要 datasets。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

# 让脚本能 `from src.extraction.schema_mapping import ...`
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from src.extraction.schema_mapping import (  # noqa: E402
    is_role_covered,
    is_type_covered,
    map_event_type,
    map_role,
)


def _convert_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # 官方 DuEE 1.0 格式：event_type / trigger(字符串) / trigger_start_index /
    #                    arguments[{role, argument, argument_start_index}]
    raw_type = (event.get("event_type") or "").strip()
    if not raw_type:
        return None

    trigger_text = (event.get("trigger") or "").strip()
    trigger_start = event.get("trigger_start_index")
    trigger_span: Optional[Tuple[int, int]] = None
    if trigger_text and isinstance(trigger_start, int) and trigger_start >= 0:
        trigger_span = (trigger_start, trigger_start + len(trigger_text))

    args: List[Dict[str, Any]] = []
    for a in event.get("arguments") or []:
        role = (a.get("role") or "").strip()
        arg_text = (a.get("argument") or "").strip()
        arg_start = a.get("argument_start_index")
        if arg_text and isinstance(arg_start, int) and arg_start >= 0:
            args.append({
                "role": role,
                "mapped_role": map_role(role),
                "start": arg_start,
                "end": arg_start + len(arg_text),
                "text": arg_text,
            })

    return {
        "event_type": raw_type,
        "mapped_type": map_event_type(raw_type),
        "trigger": {
            "start": trigger_span[0],
            "end": trigger_span[1],
            "text": trigger_text,
        } if trigger_span else None,
        "arguments": args,
    }


def _convert_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    text = (row.get("text") or "").strip()
    if not text:
        return None
    events: List[Dict[str, Any]] = []
    for e in row.get("event_list") or []:
        ce = _convert_event(e)
        if ce:
            events.append(ce)
    return {"text": text, "events": events}


def _download() -> List[Dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "缺少依赖 datasets，请先执行：pip install datasets\n"
            "或改用 --no-download --input 从本地文件读取。"
        ) from exc

    ds = load_dataset("nlhappy/DuEE")
    rows: List[Dict[str, Any]] = []
    for split in ds.values():
        rows.extend(split.to_list())
    return rows


def _load_local(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # 先尝试整体 JSON（数组）；官方 DuEE 的 .json 实为 JSONL，需逐行解析。
    try:
        data = json.loads(content)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        pass
    rows: List[Dict[str, Any]] = []
    for line in content.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _report(rows: List[Dict[str, Any]], dropped_no_trigger: int) -> None:
    type_counter: Counter = Counter()
    mapped_counter: Counter = Counter()
    role_counter: Counter = Counter()
    uncovered_types: set = set()
    uncovered_roles: set = set()
    total_events = 0

    for row in rows:
        for e in row["events"]:
            total_events += 1
            type_counter[e["event_type"]] += 1
            mapped_counter[e["mapped_type"]] += 1
            if not is_type_covered(e["event_type"]):
                uncovered_types.add(e["event_type"])
            for a in e["arguments"]:
                role_counter[a["role"]] += 1
                if not is_role_covered(a["role"]):
                    uncovered_roles.add(a["role"])

    print("=" * 60)
    print(f"句子数：{len(rows)}，事件数：{total_events}")
    print(f"因无触发词被丢弃的事件数：{dropped_no_trigger}")
    print("-" * 60)
    print("映射后团队类型分布：")
    for t, c in mapped_counter.most_common():
        print(f"  {t:<8} {c}")
    print("-" * 60)
    print("原始事件类型 Top 15：")
    for t, c in type_counter.most_common(15):
        print(f"  {t:<24} {c}")
    print("-" * 60)
    print("原始论元角色 Top 15：")
    for r, c in role_counter.most_common(15):
        print(f"  {r:<16} {c}")
    if uncovered_types:
        print("-" * 60)
        print(f"⚠ 未覆盖的事件类型（{len(uncovered_types)} 个，请补入 EXPLICIT_TYPE_MAP）：")
        for t in sorted(uncovered_types):
            print(f"  {t}")
    if uncovered_roles:
        print("-" * 60)
        print(f"⚠ 未覆盖的论元角色（{len(uncovered_roles)} 个，请补入 EXPLICIT_ROLE_MAP）：")
        for r in sorted(uncovered_roles):
            print(f"  {r}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="下载 DuEE 并转换为 train_events.jsonl")
    parser.add_argument("--output", default=os.path.join(_ROOT, "data", "raw", "train_events.jsonl"),
                        help="输出 JSONL 路径")
    parser.add_argument("--no-download", action="store_true", help="不联网下载，从 --input 读取")
    parser.add_argument("--input", default="", help="本地数据文件（JSON 数组或 JSONL）")
    parser.add_argument("--max-samples", type=int, default=0, help="调试用：只取前 N 条")
    parser.add_argument("--keep-no-trigger", action="store_true",
                        help="保留无触发词的事件（默认丢弃）")
    args = parser.parse_args()

    if args.input:
        raw_rows = _load_local(args.input)
    elif args.no_download:
        raise SystemExit("--no-download 需要同时指定 --input")
    else:
        local_default = os.path.join(_ROOT, "data", "raw", "DuEE", "duee_train.json")
        if os.path.exists(local_default):
            print(f"使用本地官方数据：{local_default}")
            raw_rows = _load_local(local_default)
        else:
            raw_rows = _download()

    if args.max_samples > 0:
        raw_rows = raw_rows[:args.max_samples]

    rows: List[Dict[str, Any]] = []
    dropped_no_trigger = 0
    for r in raw_rows:
        row = _convert_row(r)
        if not row:
            continue
        if not args.keep_no_trigger:
            before = len(row["events"])
            row["events"] = [e for e in row["events"] if e["trigger"] is not None]
            dropped_no_trigger += before - len(row["events"])
        if row["events"]:  # 空句不落盘
            rows.append(row)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    _report(rows, dropped_no_trigger)
    print(f"\n已写出 {len(rows)} 行 -> {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
