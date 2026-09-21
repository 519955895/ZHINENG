"""模块1 主接口：规则版事件抽取基线（成员 A）。

这是一个**可跑的基线**，用于打通全流程。成员 A 在此基础上替换为
NER / 序列标注 / 生成式模型即可（函数签名不变）：
    extract_events(documents: List[Document]) -> List[Event]

基线思路：
1. 按句号/换行切句；
2. 句内再按因果连接词与逗号切出"原子事件片段"；
3. 片段命中触发词词典即生成一个事件；
4. 简单规则抽取时间（日期）与地点（X市），并按原文片段去重。
"""
from __future__ import annotations

import re
from typing import List

from ..common.schemas import Argument, Document, Event

# 触发词 -> 事件类型（成员 A 可扩充/换成模型）
TRIGGER_MAP = {
    "灾害/事故": ["暴雨", "强降雨", "积水", "内涝", "抛锚", "追尾", "事故",
                  "火灾", "地震", "洪水", "坍塌", "爆炸", "泄漏", "车祸"],
    "政策/发布": ["宣布", "出台", "发布", "颁布", "实施", "签约", "施行"],
    "经济/涨跌": ["上涨", "下跌", "暴跌", "大涨", "裁员", "涨价", "降价", "涨停", "亏损"],
    "社会/舆情": ["瘫痪", "拥堵", "受阻", "滞留", "抗议", "罢工", "抢购", "恐慌", "停课"],
}

# 句内切分符：因果连接词 + 逗号（把"暴雨导致积水，造成瘫痪"切成原子片段）
_SPLIT_RE = re.compile(r"(导致|造成|引发|引起|致使|使得|从而|因此|所以|影响|，|,)")
_SENT_SPLIT = re.compile(r"[。！？!?；;\n]+")
_DATE_RE = re.compile(r"(\d{4}年)?\d{1,2}月\d{1,2}日?")
_LOC_RE = re.compile(r"[\u4e00-\u9fa5]{2,6}市")

# 片段开头的连接词/指示词，抽取时剥掉
_LEAD_CUES = ["受", "因", "由于", "因为", "并且", "而且", "然后", "随后", "该", "这"]


def _clean(seg: str) -> str:
    seg = seg.strip(" ，。、,.;；")
    for w in _LEAD_CUES:
        if seg.startswith(w):
            seg = seg[len(w):].lstrip(" ，。、,.;；")
            break
    return seg.strip(" ，。、,.;；")


def _match_trigger(seg: str):
    for etype, words in TRIGGER_MAP.items():
        for w in words:
            if w in seg:
                return etype, w
    return None, None


def extract_events(documents: List[Document]) -> List[Event]:
    events: List[Event] = []
    seen = set()
    eid = 0
    for doc in documents:
        for sent in _SENT_SPLIT.split(doc.text):
            for seg in _SPLIT_RE.split(sent):
                seg = _clean(seg)
                if not seg:
                    continue
                etype, trigger = _match_trigger(seg)
                if etype is None:
                    continue
                # 去重：同文档内、同一触发词视为同一事件（事件共指的简单近似）
                # 局限：通用触发词（如"事故"）可能把不同事件误合并，升级版可换语义相似度
                if (doc.doc_id, trigger) in seen:
                    continue
                seen.add((doc.doc_id, trigger))
                eid += 1
                args: List[Argument] = []
                loc = ""
                m = _LOC_RE.search(seg)
                if m:
                    loc = m.group(0)
                    args.append(Argument(role="location", value=loc))
                t = ""
                m = _DATE_RE.search(seg)
                if m:
                    t = m.group(0)
                events.append(Event(
                    event_id=f"E{eid:03d}",
                    doc_id=doc.doc_id,
                    event_type=etype,
                    trigger=trigger,
                    mention=seg,
                    arguments=args,
                    time=t or doc.publish_time,
                    location=loc,
                    char_offset=None,
                    confidence=0.8,
                ))
    return events
