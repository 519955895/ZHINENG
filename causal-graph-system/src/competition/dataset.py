"""竞赛数据包加载器。

数据包目录约定（A/B/C 三档）：
    D001.txt ... Dnnn.txt          原始文档（每行结构：首行标题，其余正文）
    事件列表.json                   A/B 档提供（C 档缺省，需系统自行抽取）
    事件因果关系列表.json            仅 A 档提供
    问题.json                       每包 7~10 个问题

本模块负责：
1. 识别档位（有事件+关系=A；有事件无关系=B；只有文档=C）；
2. 把赛题字段映射为系统统一 schema（Event / CausalRelation / Document）；
3. 从问题文本中收集 Dxxx（阶段标签）提示（如 D001（事故发生）），供 C 档抽取与锚定使用。
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..common.schemas import Argument, CausalRelation, Document, Event

EVENTS_FILE = "事件列表.json"
RELATIONS_FILE = "事件因果关系列表.json"
QUESTIONS_FILE = "问题.json"

# 置信度档位 -> 数值
LEVEL_TO_CONF = {
    "certain": 0.9,
    "probable": 0.65,
    "possible": 0.45,
    "likely": 0.6,
    "uncertain": 0.3,
}

_DOC_RE = re.compile(r"^D(\d+)\.txt$", re.IGNORECASE)
_ID_LABEL_RE = re.compile(r"D(\d{3,4})[（(]\s*([^）)]{1,20}?)\s*[）)]")


@dataclass
class Pack:
    """一个竞赛数据包的全部输入。"""
    pack_dir: str
    pack_name: str
    task: str                                   # "A" / "B" / "C"
    docs: List[Document] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    relations: List[CausalRelation] = field(default_factory=list)
    questions: List[dict] = field(default_factory=list)
    label_hints: Dict[str, str] = field(default_factory=dict)
    given_events: bool = False
    given_relations: bool = False

    def doc_map(self) -> Dict[str, Document]:
        return {d.doc_id: d for d in self.docs}

    def event_map(self) -> Dict[str, Event]:
        return {e.event_id: e for e in self.events}


def detect_task(pack_dir: str) -> str:
    """按文件存在性判定档位。"""
    has_events = os.path.isfile(os.path.join(pack_dir, EVENTS_FILE))
    has_relations = os.path.isfile(os.path.join(pack_dir, RELATIONS_FILE))
    if has_relations and has_events:
        return "A"
    if has_events:
        return "B"
    return "C"


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_documents(pack_dir: str) -> List[Document]:
    docs: List[Document] = []
    names = []
    for fn in os.listdir(pack_dir):
        m = _DOC_RE.match(fn)
        if m:
            names.append((int(m.group(1)), fn))
    for _, fn in sorted(names):
        path = os.path.join(pack_dir, fn)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        doc_id = os.path.splitext(fn)[0]
        title = lines[0] if lines else ""
        docs.append(Document(doc_id=doc_id, title=title, text=raw, source=""))
    return docs


def _map_event(raw: dict, doc_title: str = "") -> Event:
    """赛题事件 JSON -> 系统 Event。"""
    arg = raw.get("argument") or {}
    arguments: List[Argument] = []
    for role, value in arg.items():
        if value:
            arguments.append(Argument(role=str(role), value=str(value)))

    mention = arg.get("内容") or doc_title or raw.get("event_type", "")
    start = raw.get("start")
    end = raw.get("end")
    offset = (int(start), int(end)) if isinstance(start, int) and isinstance(end, int) else None

    return Event(
        event_id=raw["event_id"],
        doc_id=raw.get("doc_id") or raw["event_id"],
        event_type=raw.get("event_type", "") or "",
        trigger=raw.get("trigger_word", "") or "",
        mention=mention,
        arguments=arguments,
        time=raw.get("occur_time", "") or "",
        location=arg.get("地点", "") or "",
        char_offset=offset,
        confidence=0.95,
    )


def _find_evidence_sentence(effect_doc: Optional[Document], cause: Event) -> List[str]:
    """在"果"文档中找一句包含因果提示词与因事件线索的原文证据。"""
    if effect_doc is None:
        return []
    cues = ("导致", "造成", "引发", "引起", "促使", "进而", "因此", "为此",
            "随之", "随后", "继而", "从而", "推动", "由于", "起因")
    clues = [w for w in (cause.event_type, cause.trigger) if w and len(w) >= 2]
    for sent in re.split(r"[。！？；\n]", effect_doc.text or ""):
        sent = sent.strip()
        if len(sent) < 6:
            continue
        if any(c in sent for c in cues) and any(cl in sent for cl in clues):
            return [sent]
    return []


def _map_relations(raw_list: list, pack: Pack) -> List[CausalRelation]:
    """赛题因果关系 JSON -> 系统 CausalRelation，并回填原文证据。"""
    doc_map = pack.doc_map()
    event_map = pack.event_map()
    relations: List[CausalRelation] = []
    for i, raw in enumerate(raw_list, 1):
        cause_id = raw["cause_event_id"]
        effect_id = raw.get("result_event_id") or raw.get("effect_event_id")
        if not cause_id or not effect_id:
            continue
        if cause_id not in event_map or effect_id not in event_map:
            continue
        cause = event_map[cause_id]
        level = (raw.get("confidence_level") or "").lower()
        rtype = raw.get("causal_type") or raw.get("relation_type") or "causal"
        desc = raw.get("description")
        evidence = _find_evidence_sentence(doc_map.get(effect_id), cause)
        if not evidence and desc:
            evidence = [str(desc)]
        if not evidence:
            evidence = [f"{cause_id}（{cause.event_type or cause.trigger}）"
                        f" → {effect_id}（{event_map[effect_id].event_type}）"]
        relations.append(CausalRelation(
            relation_id=f"R{i:03d}",
            cause_event_id=cause_id,
            effect_event_id=effect_id,
            relation_type=rtype,
            evidence=evidence,
            confidence=LEVEL_TO_CONF.get(level, 0.6),
            time_lag="",
        ))
    return relations


def _collect_label_hints(questions: List[dict], events: List[Event]) -> Dict[str, str]:
    """从问题的 Dxxx（标签）表述收集事件阶段标签。"""
    hints: Dict[str, str] = {}
    for q in questions:
        for m in _ID_LABEL_RE.finditer(q.get("question", "")):
            eid, label = f"D{m.group(1)}", m.group(2).strip()
            if label and eid not in hints:
                hints[eid] = label
    # 已给事件列表的标签更权威
    for e in events:
        if e.event_type:
            hints[e.event_id] = e.event_type
    return hints


def load_pack(pack_dir: str, task: Optional[str] = None) -> Pack:
    """加载一个数据包。task 可强制指定（A/B/C），否则按文件自动识别。"""
    pack_dir = os.path.abspath(pack_dir)
    pack_name = os.path.basename(pack_dir.rstrip(r"\/"))
    detected = detect_task(pack_dir)
    task = task or detected

    docs = _load_documents(pack_dir)
    doc_title_map = {d.doc_id: d.title for d in docs}

    given_events = detected in ("A", "B")
    events: List[Event] = []
    if given_events:
        for raw in _read_json(os.path.join(pack_dir, EVENTS_FILE)):
            events.append(_map_event(raw, doc_title_map.get(raw.get("doc_id"), "")))

    questions = _read_json(os.path.join(pack_dir, QUESTIONS_FILE))

    pack = Pack(
        pack_dir=pack_dir,
        pack_name=pack_name,
        task=task,
        docs=docs,
        events=events,
        questions=questions,
        given_events=given_events,
        given_relations=(detected == "A"),
    )

    if detected == "A":
        pack.relations = _map_relations(
            _read_json(os.path.join(pack_dir, RELATIONS_FILE)), pack)

    pack.label_hints = _collect_label_hints(questions, events)
    return pack
