#!/usr/bin/env python
"""训练模块1事件抽取模型（roberta-wwm-ext + PAIE 式跨度选择，成员 A）。

用法：
    python scripts/train_extraction.py \
        --data data/raw/train_events.jsonl \
        --plm hfl/chinese-roberta-wwm-ext \
        --out models/extraction/best.pt

依赖：pip install torch transformers

说明：
- 训练数据来自 scripts/prepare_duee_data.py 生成的 train_events.jsonl；
- 事件类型用 mapped_type（团队 4 类），角色用 mapped_role（通用角色），trigger 作为特殊角色（a 方案）；
- 每个「事件 × 角色」展开为一个训练样本，预测该角色的论元 start/end；
- 无该角色的样本标注为「无答案」（start=end=[CLS] 位置）。
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer

from src.extraction.models import EVENT_TYPES, PAieExtractor, ROLES

# 类型/角色 -> id
TYPE2ID = {t: i for i, t in enumerate(EVENT_TYPES)}
ROLE2ID = {r: i for i, r in enumerate(ROLES)}
NUM_TYPES = len(EVENT_TYPES)
NUM_ROLES = len(ROLES)


def _char_to_token_map(offset_mapping: List[Tuple[int, int]]) -> Dict[int, int]:
    """字符索引 -> token 索引（用 offset_mapping 构建）。"""
    m: Dict[int, int] = {}
    for tok_idx, (s, e) in enumerate(offset_mapping):
        for c in range(s, e):
            m[c] = tok_idx
    return m


def _span_to_tokens(span: Optional[Tuple[int, int]],
                    char2tok: Dict[int, int]) -> Optional[Tuple[int, int]]:
    """字符半开区间 (start, end) -> token 闭区间 (start_tok, end_tok)。"""
    if span is None:
        return None
    start, end = span
    s = char2tok.get(start)
    e = char2tok.get(end - 1)  # 半开区间最后一个字符
    if s is None or e is None:
        return None
    return s, e


def build_samples(rows: List[Dict[str, Any]], tokenizer, max_len: int) -> List[Dict[str, Any]]:
    """把 train_events.jsonl 展开为「事件 × 角色」训练样本。"""
    samples: List[Dict[str, Any]] = []
    for row in rows:
        text = row.get("text", "")
        events = row.get("events") or []
        if not text or not events:
            continue

        # 该句事件类型的多标签
        type_ids_set = {TYPE2ID[e["mapped_type"]] for e in events if e.get("mapped_type") in TYPE2ID}
        type_labels = [1 if i in type_ids_set else 0 for i in range(NUM_TYPES)]

        enc = tokenizer(text, return_offsets_mapping=True, max_length=max_len,
                        truncation=True, padding=False)
        input_ids = enc["input_ids"]
        attention_mask = enc["attention_mask"]
        char2tok = _char_to_token_map(enc["offset_mapping"])

        for e in events:
            tid = TYPE2ID.get(e.get("mapped_type"))
            if tid is None:
                continue

            trigger_span = None
            if e.get("trigger"):
                trigger_span = (e["trigger"]["start"], e["trigger"]["end"])

            # 角色 -> 字符 span（每个角色取第一个论元）
            role_spans: Dict[str, Tuple[int, int]] = {}
            for a in e.get("arguments") or []:
                r = a.get("mapped_role")
                if r in ROLE2ID and r not in role_spans:
                    role_spans[r] = (a["start"], a["end"])

            for role in ROLES:
                rid = ROLE2ID[role]
                span = trigger_span if role == "trigger" else role_spans.get(role)
                if span is None:
                    # 负样本：该 (事件, 角色) 无此论元 -> 标注「无答案」[CLS] 位置（token 0）。
                    # 否则模型只会见过“每个角色都有 span”的正例，推理时对每个角色都强行输出
                    # 一个 span，学不会“该角色不存在”，从而抽出大量错误论元。
                    start_label = end_label = 0
                else:
                    tok = _span_to_tokens(span, char2tok)
                    if tok is None:
                        continue  # 论元被 max_len 截断/越界，无法标注，跳过
                    start_label, end_label = tok
                samples.append({
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "type_id": tid,
                    "role_id": rid,
                    "type_labels": type_labels,
                    "start_label": start_label,
                    "end_label": end_label,
                })
    return samples


class ExtractionDataset(Dataset):
    def __init__(self, samples: List[Dict[str, Any]]):
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        s = self.samples[idx]
        return {
            "input_ids": torch.tensor(s["input_ids"], dtype=torch.long),
            "attention_mask": torch.tensor(s["attention_mask"], dtype=torch.long),
            "type_id": s["type_id"],
            "role_id": s["role_id"],
            "type_labels": torch.tensor(s["type_labels"], dtype=torch.float),
            "start_label": s["start_label"],
            "end_label": s["end_label"],
        }


def collate_fn(batch: List[Dict[str, Any]], pad_token_id: int):
    input_ids = pad_sequence([b["input_ids"] for b in batch], batch_first=True,
                             padding_value=pad_token_id)
    attention_mask = pad_sequence([b["attention_mask"] for b in batch], batch_first=True,
                                  padding_value=0)
    type_ids = torch.tensor([b["type_id"] for b in batch], dtype=torch.long)
    role_ids = torch.tensor([b["role_id"] for b in batch], dtype=torch.long)
    type_labels = torch.stack([b["type_labels"] for b in batch])
    start_labels = torch.tensor([b["start_label"] for b in batch], dtype=torch.long)
    end_labels = torch.tensor([b["end_label"] for b in batch], dtype=torch.long)
    return input_ids, attention_mask, type_ids, role_ids, type_labels, start_labels, end_labels


def _forward_loss(model, batch, device, type_crit, span_crit):
    (input_ids, attention_mask, type_ids, role_ids,
     type_labels, start_labels, end_labels) = batch
    input_ids = input_ids.to(device)
    attention_mask = attention_mask.to(device)
    type_ids = type_ids.to(device)
    role_ids = role_ids.to(device)
    type_labels = type_labels.to(device)
    start_labels = start_labels.to(device)
    end_labels = end_labels.to(device)

    type_logits, start_logits, end_logits = model(
        input_ids, attention_mask, type_ids, role_ids)
    type_loss = type_crit(type_logits, type_labels)
    start_loss = span_crit(start_logits, start_labels)
    end_loss = span_crit(end_logits, end_labels)
    total = type_loss + start_loss + end_loss
    return total, type_loss.item(), (start_loss + end_loss).item()


def train(args) -> None:
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu") \
        if args.device == "auto" else torch.device(args.device)
    print(f"设备：{device}")

    with open(args.data, "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    print(f"读入 {len(rows)} 句")

    tokenizer = AutoTokenizer.from_pretrained(args.plm, use_fast=True)
    samples = build_samples(rows, tokenizer, args.max_len)
    print(f"展开为 {len(samples)} 个「事件×角色」训练样本")
    random.shuffle(samples)

    n_val = max(1, int(len(samples) * args.val_split))
    train_ds = ExtractionDataset(samples[n_val:])
    val_ds = ExtractionDataset(samples[:n_val])
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                          collate_fn=lambda b: collate_fn(b, tokenizer.pad_token_id))
    val_dl = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                        collate_fn=lambda b: collate_fn(b, tokenizer.pad_token_id))

    model = PAieExtractor(plm_name=args.plm).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    type_crit = nn.BCEWithLogitsLoss()
    span_crit = nn.CrossEntropyLoss()

    best_val = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_dl:
            optimizer.zero_grad()
            loss, _, _ = _forward_loss(model, batch, device, type_crit, span_crit)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_dl:
                loss, _, _ = _forward_loss(model, batch, device, type_crit, span_crit)
                val_loss += loss.item()

        avg = total_loss / max(len(train_dl), 1)
        val_avg = val_loss / max(len(val_dl), 1)
        print(f"epoch {epoch}/{args.epochs} | train_loss {avg:.4f} | val_loss {val_avg:.4f}")

        if val_avg < best_val:
            best_val = val_avg
            model.save(args.out, extra={
                "type2id": TYPE2ID,
                "role2id": ROLE2ID,
                "max_len": args.max_len,
            })
            print(f"  -> 保存最佳模型 -> {os.path.abspath(args.out)}")

    print(f"训练完成，best val_loss = {best_val:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="训练事件抽取模型（roberta-wwm-ext + PAIE）")
    parser.add_argument("--data", default=os.path.join(_ROOT, "data", "raw", "train_events.jsonl"))
    parser.add_argument("--plm", default="hfl/chinese-roberta-wwm-ext")
    parser.add_argument("--out", default=os.path.join(_ROOT, "models", "extraction", "best.pt"))
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-len", type=int, default=256)
    parser.add_argument("--val-split", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
