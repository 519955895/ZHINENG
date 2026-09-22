"""模块1 事件抽取模型：roberta-wwm-ext + PAIE 式跨度选择（成员 A）。

架构（对应成员 A 的方案）：
1. 文本编码：中文 RoBERTa（默认 hfl/chinese-roberta-wwm-ext），输出 token 级表示；
2. 事件类型判断：[CLS] -> 4 类多标签 sigmoid；
3. 多事件识别与论元抽取：对每个 (事件类型, 角色) 组合，用可学习 query 与 token
   表示点积打分，预测论元的 start/end 位置；trigger 作为特殊角色一并预测（a 方案）。

对外只暴露 PAieExtractor 与常量，训练脚本与推理入口共用，保证 train/infer 一致。
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

import torch
import torch.nn as nn
from transformers import AutoModel

from .schema_mapping import TEAM_EVENT_TYPES, TEAM_ROLES

# 团队 4 类事件类型（与 schema_mapping / docs/interface.md 一致）
EVENT_TYPES: List[str] = list(TEAM_EVENT_TYPES)
# 论元角色 = 触发词（a 方案） + 7 个通用角色
ROLES: List[str] = ["trigger"] + list(TEAM_ROLES)


class PAieExtractor(nn.Module):
    """roberta-wwm-ext 编码器 + 类型多标签头 + query 式跨度选择器。"""

    def __init__(self, plm_name: str, num_types: Optional[int] = None,
                 roles: Optional[List[str]] = None, dropout: float = 0.1):
        super().__init__()
        self.plm_name = plm_name
        self.roles: List[str] = list(roles) if roles else ROLES
        self.num_types = num_types if num_types is not None else len(EVENT_TYPES)
        self.num_roles = len(self.roles)
        self.max_len = 256  # 推理时句子最大长度，训练脚本通过 extra 覆盖后随权重保存

        self.encoder = AutoModel.from_pretrained(plm_name)
        hidden = self.encoder.config.hidden_size

        self.dropout = nn.Dropout(dropout)

        # 事件类型多标签分类头
        self.type_cls = nn.Linear(hidden, self.num_types)

        # (类型, 角色) -> query 向量（PAIE prompt 的向量化表示）
        self.type_embedding = nn.Embedding(self.num_types, hidden)
        self.role_embedding = nn.Embedding(self.num_roles, hidden)

        # query 投影到 start/end 打分空间
        self.start_proj = nn.Linear(hidden, hidden)
        self.end_proj = nn.Linear(hidden, hidden)

    def _query(self, type_ids: torch.Tensor, role_ids: torch.Tensor) -> torch.Tensor:
        return self.type_embedding(type_ids) + self.role_embedding(role_ids)

    def forward(self, input_ids, attention_mask, type_ids, role_ids):
        enc = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        hidden_states = enc.last_hidden_state  # (B, L, H)
        cls = hidden_states[:, 0, :]

        type_logits = self.type_cls(self.dropout(cls))  # (B, num_types)

        q = self._query(type_ids, role_ids)              # (B, H)
        start_logits = torch.einsum("blh,bh->bl", hidden_states, self.start_proj(q))
        end_logits = torch.einsum("blh,bh->bl", hidden_states, self.end_proj(q))

        return type_logits, start_logits, end_logits

    @torch.no_grad()
    def predict(self, input_ids, attention_mask, type_ids, role_ids):
        """推理：返回类型概率(sigmoid)与 start/end 概率(softmax)。"""
        self.eval()
        type_logits, start_logits, end_logits = self.forward(
            input_ids, attention_mask, type_ids, role_ids)
        type_probs = torch.sigmoid(type_logits)
        start_probs = torch.softmax(start_logits, dim=-1)
        end_probs = torch.softmax(end_logits, dim=-1)
        return type_probs, start_probs, end_probs

    def save(self, path: str, extra: Optional[Dict] = None) -> None:
        """保存权重 + 推理所需的元信息。"""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        payload = {
            "state_dict": self.state_dict(),
            "plm_name": self.plm_name,
            "num_types": self.num_types,
            "roles": self.roles,
            "max_len": getattr(self, "max_len", 256),
        }
        if extra:
            payload["extra"] = extra
        torch.save(payload, path)

    @classmethod
    def load(cls, path: str, map_location: str = "cpu") -> "PAieExtractor":
        payload = torch.load(path, map_location=map_location)
        model = cls(plm_name=payload["plm_name"], num_types=payload["num_types"],
                    roles=payload["roles"])
        model.max_len = payload.get("max_len", 256)
        model.load_state_dict(payload["state_dict"])
        model.eval()
        return model
