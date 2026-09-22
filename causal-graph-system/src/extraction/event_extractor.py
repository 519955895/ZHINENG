"""模块1 主接口：从原始新闻文档抽取原子事件（成员 A）。

技术路线（渐进式）第 1 步——规则基线（先跑通）：
- 触发词词典 + 正则定位触发词；
- 简单规则把事件类型映射到团队 4 类；
- 时间/地点用正则抽取并归一化（时间缺年份时用 publish_time 补全）；
- subject/object 等施受事论元留待 NER / 序列标注升级，规则阶段不硬填，避免误判施受事。

约束（严格遵守）：
- 函数签名 extract_events(documents: List[Document]) -> List[Event] 不变；
- event_type 只取团队 4 类；Argument.role 只取通用角色；
- event_id 全局唯一（"E" + 自增）；confidence ∈ [0,1]；
- mention 保留原文片段，char_offset 用半开区间 [start, end)，保证 text[start:end] == mention。
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from ..common.schemas import Argument, Document, Event

from .argument_role import extract_arguments

# ---------------------------------------------------------------------------
# 团队 4 类事件类型（与 docs/interface.md、configs/challenge.yaml 保持一致）
# ---------------------------------------------------------------------------
EVENT_TYPES: Tuple[str, ...] = ("灾害/事故", "政策/发布", "经济/涨跌", "社会/舆情")

# ---------------------------------------------------------------------------
# 触发词词典：触发词 -> 事件类型（技术路线第 1 步的触发词词典，可继续扩充）
# ---------------------------------------------------------------------------
_TRIGGER_MAP = {
    # 灾害/事故
    "发生": "灾害/事故", "遭遇": "灾害/事故", "导致": "灾害/事故", "造成": "灾害/事故",
    "引发": "灾害/事故", "爆发": "灾害/事故", "抛锚": "灾害/事故", "瘫痪": "灾害/事故",
    "受阻": "灾害/事故", "伤亡": "灾害/事故", "坠毁": "灾害/事故", "坍塌": "灾害/事故",
    "泄漏": "灾害/事故", "泄露": "灾害/事故", "起火": "灾害/事故", "爆炸": "灾害/事故",
    "相撞": "灾害/事故", "翻车": "灾害/事故", "倒塌": "灾害/事故", "内涝": "灾害/事故",
    "积水": "灾害/事故", "事故": "灾害/事故",
    # 政策/发布
    "宣布": "政策/发布", "出台": "政策/发布", "颁布": "政策/发布", "发布": "政策/发布",
    "签署": "政策/发布", "任命": "政策/发布", "选举": "政策/发布", "召开": "政策/发布",
    "会见": "政策/发布", "会谈": "政策/发布", "签约": "政策/发布", "推出": "政策/发布",
    "实施": "政策/发布", "通过": "政策/发布",
    # 经济/涨跌
    "上涨": "经济/涨跌", "下跌": "经济/涨跌", "下降": "经济/涨跌", "涨价": "经济/涨跌", "降价": "经济/涨跌",
    "飙升": "经济/涨跌", "暴跌": "经济/涨跌", "裁员": "经济/涨跌", "融资": "经济/涨跌",
    "上市": "经济/涨跌", "收购": "经济/涨跌", "破产": "经济/涨跌", "倒闭": "经济/涨跌",
    "亏损": "经济/涨跌", "盈利": "经济/涨跌", "增长": "经济/涨跌", "下滑": "经济/涨跌",
    # 社会/舆情
    "抗议": "社会/舆情", "集会": "社会/舆情", "罢工": "社会/舆情", "游行": "社会/舆情",
    "投诉": "社会/舆情", "维权": "社会/舆情", "拘捕": "社会/舆情", "起诉": "社会/舆情",
    "开庭": "社会/舆情", "审判": "社会/舆情", "处罚": "社会/舆情", "斗殴": "社会/舆情",
    "纠纷": "社会/舆情", "失联": "社会/舆情", "曝光": "社会/舆情", "传播": "社会/舆情",
}

_SENT_SPLIT = re.compile(r"[。！？；!?;\n]")
_TIME_RE = re.compile(r"\d{1,4}年\d{1,2}月\d{1,2}日|\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2}")
_LOCATION_RE = re.compile(r"[\u4e00-\u9fa5]{1,4}(?:省|市|县|区|镇|乡|村|国)(?![民场域界长委局府人员家])")
_YEAR_RE = re.compile(r"\d{4}")


def _split_sentences(text: str) -> List[Tuple[str, int, int]]:
    """按句末标点切句，返回 (不含标点的句子, 起始, 结束) 半开区间。"""
    out: List[Tuple[str, int, int]] = []
    start = 0
    for m in _SENT_SPLIT.finditer(text):
        end = m.start()
        if end > start:
            out.append((text[start:end], start, end))
        start = m.end()
    if start < len(text):
        out.append((text[start:], start, len(text)))
    return out


def _normalize_time(raw: str, publish_time: str) -> str:
    """把文本时间归一化为 ISO 日期；缺年份时用 publish_time 补全。"""
    raw = (raw or "").strip()
    if not raw:
        return ""
    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", raw):
        return raw
    m = re.fullmatch(r"(\d{1,4})年(\d{1,2})月(\d{1,2})日", raw)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.fullmatch(r"(\d{1,2})月(\d{1,2})日", raw)
    if m:
        ym = _YEAR_RE.search(publish_time or "")
        if ym:
            return f"{ym.group(0)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        return raw
    return raw


def _extract_time(sent: str, publish_time: str) -> str:
    m = _TIME_RE.search(sent)
    return _normalize_time(m.group(0), publish_time) if m else ""


_LEADING_PREP = "据个性对向从将把与和到于由为的在此其"


def _extract_location(sent: str) -> str:
    m = _LOCATION_RE.search(sent)
    if not m:
        return ""
    loc = m.group(0)
    # 剥掉开头虚词/量词（如"据美国" -> "美国"）；"个国/性国" 由正则负向断言排除
    while len(loc) > 1 and loc[0] in _LEADING_PREP:
        loc = loc[1:]
    return loc


def _extract_doc(doc: Document, start_id: int) -> List[Event]:
    text = doc.text or ""
    publish_time = doc.publish_time or ""
    events: List[Event] = []
    eid = start_id
    for sent, s_start, s_end in _split_sentences(text):
        # 该句命中的第一个触发词（取出现位置最早者）
        hit = None
        for trigger, etype in _TRIGGER_MAP.items():
            pos = sent.find(trigger)
            if pos != -1 and (hit is None or pos < hit[0]):
                hit = (pos, trigger, etype)
        if hit is None:
            continue
        pos, trigger, etype = hit

        time_val = _extract_time(sent, publish_time)
        loc_val = _extract_location(sent)
        args: List[Argument] = []
        if time_val:
            args.append(Argument(role="time", value=time_val))
        if loc_val:
            args.append(Argument(role="location", value=loc_val))
        # 补全施事/受事等论元（jieba 词性 + 规则，见 argument_role.py）
        args.extend(extract_arguments(sent, pos, pos + len(trigger)))

        conf = round(min(0.7 + (0.1 if time_val else 0) + (0.1 if loc_val else 0), 0.95), 2)

        events.append(Event(
            event_id=f"E{eid:03d}",
            doc_id=doc.doc_id,
            event_type=etype,
            trigger=trigger,
            mention=sent,
            arguments=args,
            time=time_val,
            location=loc_val,
            char_offset=(s_start, s_end),
            confidence=conf,
        ))
        eid += 1
    return events


def extract_events(documents: List[Document],
                   extraction_config: Optional[Dict] = None) -> List[Event]:
    """从多篇文档中抽取事件。

    默认走规则基线（技术路线第 1 步）；当 extraction_config["model"] 为 pai/ner/seq2seq 时，
    改用训练好的 PAI 模型（scripts/train_extraction.py 产出）。

    Args:
        documents: 原始新闻文档列表。
        extraction_config: 模块1 配置字典（对应 configs/*.yaml 的 extraction 段），
            支持的键：model(rule/pai)、model_path、threshold、min_confidence、device。

    Returns:
        Event 列表；每个事件携带 doc_id、mention、arguments、char_offset 等。
    """
    cfg = extraction_config or {}
    model = (cfg.get("model") or "rule").lower()
    if model in ("pai", "pai-extractor", "ner", "seq2seq"):
        from . import pai_inference  # 延迟导入，避免与 pai_inference 形成环依赖
        return pai_inference.extract_events_pai(
            documents,
            model_path=cfg.get("model_path"),
            threshold=float(cfg.get("threshold", 0.5)),
            min_confidence=float(cfg.get("min_confidence", 0.5)),
            device=cfg.get("device", "auto"),
        )

    events: List[Event] = []
    next_id = 1
    for doc in documents:
        doc_events = _extract_doc(doc, next_id)
        events.extend(doc_events)
        next_id += len(doc_events)
    return events
