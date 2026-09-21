"""统一数据结构（三人协作契约）。

本文件是全系统的"数据宪法"：三个模块之间只通过这里的类型进行交接。
任何字段的增删改都必须同步更新 docs/interface.md，并在团队内沟通。

约定：
- 中间产物落盘统一用 JSON（list 用 JSONL，单对象用 JSON）。
- 所有 from_dict/to_dict 方法保证跨模块、跨语言（未来如需 C++/Java 端）可互转。
- event_id / relation_id / doc_id 全系统唯一，前缀建议：D=文档, E=事件, R=关系, G=图。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# 输入：原始文档
# --------------------------------------------------------------------------

@dataclass
class Document:
    """一篇原始新闻文档（系统最上游输入）。"""
    doc_id: str
    title: str
    text: str
    source: str = ""                    # 来源媒体
    publish_time: str = ""              # 发布时间，ISO 格式 "2024-07-01"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Document":
        return cls(**d)


# --------------------------------------------------------------------------
# 模块1 产物：事件
# --------------------------------------------------------------------------

@dataclass
class Argument:
    """事件论元：谁(who)在何时(when)何地(where)对谁(whom)做了什么(what)。"""
    role: str                           # subject/object/time/location/instrument/...
    value: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Argument":
        return cls(**d)


@dataclass
class Event:
    """一个抽取出来的原子事件。模块1产出、模块2消费、模块3作为图谱节点。"""
    event_id: str
    doc_id: str
    event_type: str                     # 事件类型，如 "灾害/事故" "政策/发布" "经济/涨跌"
    trigger: str                        # 触发词，如 "发生" "宣布" "上涨"
    mention: str                        # 原文片段，用于追溯证据
    arguments: List[Argument] = field(default_factory=list)
    time: str = ""                      # 归一化时间
    location: str = ""                  # 归一化地点
    char_offset: Optional[Tuple[int, int]] = None   # 在原文中的 (start, end) 字符偏移
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Event":
        d = dict(d)
        d["arguments"] = [Argument.from_dict(a) for a in d.get("arguments", [])]
        d["char_offset"] = tuple(d["char_offset"]) if d.get("char_offset") else None
        return cls(**d)

    def get_arg(self, role: str) -> Optional[str]:
        for a in self.arguments:
            if a.role == role:
                return a.value
        return None


# --------------------------------------------------------------------------
# 模块2 产物：因果关系
# --------------------------------------------------------------------------

# 关系类型约定
RELATION_CAUSAL = "causal"          # 直接因果：A 导致 B
RELATION_ENABLES = "enables"        # 使能：A 使 B 成为可能
RELATION_PREVENTS = "prevents"      # 抑制：A 阻止 B
RELATION_CONDITIONAL = "conditional"  # 条件：若 A 则 B


@dataclass
class CausalRelation:
    """一条因果边：cause -> effect。模块2产出、模块3消费。"""
    relation_id: str
    cause_event_id: str
    effect_event_id: str
    relation_type: str = RELATION_CAUSAL
    evidence: List[str] = field(default_factory=list)   # 原文证据片段（务必保留）
    confidence: float = 0.0
    time_lag: str = ""                  # 可选："immediate" / "days" / "years"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CausalRelation":
        return cls(**d)


# --------------------------------------------------------------------------
# 模块3 产物：因果图谱
# --------------------------------------------------------------------------

@dataclass
class CausalGraph:
    """因果有向图：节点=事件，边=因果关系。"""
    graph_id: str
    nodes: List[Event] = field(default_factory=list)
    edges: List[CausalRelation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CausalGraph":
        return cls(
            graph_id=d["graph_id"],
            nodes=[Event.from_dict(n) for n in d.get("nodes", [])],
            edges=[CausalRelation.from_dict(e) for e in d.get("edges", [])],
            metadata=d.get("metadata", {}),
        )

    def node_map(self) -> Dict[str, Event]:
        return {n.event_id: n for n in self.nodes}


# --------------------------------------------------------------------------
# 推理问答：问题与答案
# --------------------------------------------------------------------------

# 问题类型约定
QT_CAUSAL_TRACING = "causal_tracing"        # 因果追溯：什么导致/由什么导致
QT_SITUATION_DEDUCTION = "situation_deduction"  # 态势推演：接下来可能发生什么
QT_COUNTERFACTUAL = "counterfactual"        # 反事实：假如 A 没发生，B 会怎样


@dataclass
class Query:
    """推理问题（赛题给的标准问题，也可能是系统内部拆解后的子问题）。"""
    query_id: str
    question: str
    question_type: str = QT_CAUSAL_TRACING
    seed_event_ids: List[str] = field(default_factory=list)   # 问题锚定的事件

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Query":
        return cls(**d)


@dataclass
class Answer:
    """推理答案，必须携带证据链（evidence_chain），保证可解释性。"""
    query_id: str
    question_type: str
    answer_text: str
    evidence_chain: List[str] = field(default_factory=list)   # 命中的边/节点 id 有序序列
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Answer":
        return cls(**d)


# --------------------------------------------------------------------------
# JSON / JSONL 序列化工具（供各模块落盘）
# --------------------------------------------------------------------------

def dumps(obj) -> str:
    return json.dumps(obj.to_dict(), ensure_ascii=False, indent=2)


def write_jsonl(path: str, objects) -> None:
    """把一组 dataclass 对象按行写为 JSONL。"""
    with open(path, "w", encoding="utf-8") as f:
        for o in objects:
            f.write(json.dumps(o.to_dict(), ensure_ascii=False) + "\n")


def read_jsonl(path: str, cls):
    """从 JSONL 读回一组 dataclass 对象。"""
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(cls.from_dict(json.loads(line)))
    return out


def write_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(dumps(obj))


def read_json(path: str, cls):
    with open(path, "r", encoding="utf-8") as f:
        return cls.from_dict(json.loads(f.read()))
