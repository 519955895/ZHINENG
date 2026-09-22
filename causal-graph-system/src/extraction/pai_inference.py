"""模块1 · PAI 模型推理：把训练好的 PAieExtractor 用于事件抽取（成员 A）。

职责：
1. 载入 scripts/train_extraction.py 产出的权重（PAieExtractor.load）+ tokenizer；
2. 对每句执行 (事件类型, 角色) query 解码：sigmoid 判类型 + softmax 定位 start/end；
3. 把 token span 转回字符偏移，组装为契约 Event。

与训练脚本共享 EVENT_TYPES / ROLES / PAieExtractor，保证 train/infer 一致。
解码规则与训练标注严格对应：start=end=[CLS](token 0) 视为「无答案」。
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import torch
from transformers import AutoTokenizer

from ..common.schemas import Argument, Document, Event
from .event_extractor import _normalize_time, _split_sentences
from .models import EVENT_TYPES, PAieExtractor, ROLES

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_MODEL_PATH = os.path.join(_ROOT, "models", "extraction", "best.pt")

_TRIGGER = "trigger"
_ABSENT = 0  # 「无答案」的 [CLS] token 下标，与训练一致

_TYPE2ID: Dict[str, int] = {t: i for i, t in enumerate(EVENT_TYPES)}
_ROLE2ID: Dict[str, int] = {r: i for i, r in enumerate(ROLES)}


class PaiExtractor:
    """封装模型 + tokenizer，提供文档级事件抽取。"""

    def __init__(self, model_path: str, device: str = "auto",
                 threshold: float = 0.5, min_confidence: float = 0.5):
        self.threshold = threshold
        self.min_confidence = min_confidence
        self.device = device if device != "auto" else (
            "cuda" if torch.cuda.is_available() else "cpu")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"未找到 PAI 模型权重：{model_path}。"
                f"请先运行 scripts/train_extraction.py 训练。")

        self.model = PAieExtractor.load(model_path, map_location="cpu").to(self.device)
        self.model.eval()
        self.max_len = getattr(self.model, "max_len", 256)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model.plm_name, use_fast=True)

        self.num_types = len(EVENT_TYPES)
        self.num_roles = len(ROLES)
        # 预构建 (类型, 角色) query 下标，解码时一次 forward 即可覆盖所有组合
        self._queries: List[Tuple[int, int]] = [
            (ti, ri) for ti in range(self.num_types) for ri in range(self.num_roles)
        ]

    def extract(self, documents: List[Document]) -> List[Event]:
        events: List[Event] = []
        eid = 1
        for doc in documents:
            for sent, s_start, s_end in _split_sentences(doc.text or ""):
                for ev in self._decode_sentence(doc, sent, s_start, s_end):
                    if ev.confidence < self.min_confidence:
                        continue
                    ev.event_id = f"E{eid:03d}"
                    eid += 1
                    events.append(ev)
        return events

    def _decode_sentence(self, doc: Document, sent: str,
                         s_start: int, s_end: int) -> List[Event]:
        enc = self.tokenizer(sent, return_offsets_mapping=True,
                             max_length=self.max_len, truncation=True, padding=False)
        input_ids = torch.tensor([enc["input_ids"]], dtype=torch.long, device=self.device)
        attention_mask = torch.tensor([enc["attention_mask"]], dtype=torch.long,
                                      device=self.device)
        offset_mapping = enc["offset_mapping"]

        # 一次 forward：batch = 所有 (类型, 角色) query，共享同一句的 token 表示
        b = len(self._queries)
        batch_input_ids = input_ids.repeat(b, 1)
        batch_mask = attention_mask.repeat(b, 1)
        type_ids = torch.tensor([q[0] for q in self._queries], dtype=torch.long,
                                device=self.device)
        role_ids = torch.tensor([q[1] for q in self._queries], dtype=torch.long,
                                device=self.device)

        type_probs, start_probs, end_probs = self.model.predict(
            batch_input_ids, batch_mask, type_ids, role_ids)
        type_prob = type_probs[0]  # (num_types,)：每行相同，取第一行

        out: List[Event] = []
        for ti, t in enumerate(EVENT_TYPES):
            p_type = float(type_prob[ti])
            if p_type < self.threshold:
                continue

            # 触发词：trigger 角色在 ROLES 下标为 0（见 models.py）
            q_trig = ti * self.num_roles + _ROLE2ID[_TRIGGER]
            trigger_span = self._argmax_span(start_probs[q_trig], end_probs[q_trig],
                                             offset_mapping)
            if trigger_span is None:
                continue  # 判定类型存在但无触发词 -> 丢弃
            trigger_text = sent[trigger_span[0]:trigger_span[1]]

            args: List[Argument] = []
            time_val = ""
            loc_val = ""
            for r in ROLES:
                if r == _TRIGGER:
                    continue
                qr = ti * self.num_roles + _ROLE2ID[r]
                span = self._argmax_span(start_probs[qr], end_probs[qr], offset_mapping)
                if span is None:
                    continue
                val = sent[span[0]:span[1]]
                args.append(Argument(role=r, value=val))
                if r == "time":
                    time_val = _normalize_time(val, doc.publish_time or "")
                elif r == "location":
                    loc_val = val

            out.append(Event(
                event_id="",  # 由 extract() 统一编号
                doc_id=doc.doc_id,
                event_type=t,
                trigger=trigger_text,
                mention=sent,
                arguments=args,
                time=time_val,
                location=loc_val,
                char_offset=(s_start, s_end),  # 保证 text[s_start:s_end] == mention
                confidence=round(p_type, 4),
            ))
        return out

    @staticmethod
    def _argmax_span(start_probs, end_probs, offset_mapping) -> Optional[Tuple[int, int]]:
        """token 概率 -> 字符半开区间；[CLS](token 0) 视为无答案，返回 None。"""
        start_pos = int(start_probs.argmax())
        end_pos = int(end_probs.argmax())
        if start_pos == _ABSENT or end_pos == _ABSENT:
            return None
        if start_pos > end_pos:
            return None
        char_start = offset_mapping[start_pos][0]
        char_end = offset_mapping[end_pos][1]
        if char_end <= char_start:
            return None
        return (char_start, char_end)


def extract_events_pai(documents: List[Document], model_path: Optional[str] = None,
                       threshold: float = 0.5, min_confidence: float = 0.5,
                       device: str = "auto") -> List[Event]:
    """用训练好的 PAI 模型从文档抽取事件（模块1 · 模型版）。"""
    path = model_path or DEFAULT_MODEL_PATH
    extractor = PaiExtractor(path, device=device, threshold=threshold,
                             min_confidence=min_confidence)
    return extractor.extract(documents)

