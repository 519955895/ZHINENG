"""C 档事件抽取适配：每篇文档抽一个主事件，事件 id 沿用文档 id（D00x）。

赛题 C 档不提供事件列表，且问题以 D00x（阶段标签）指代事件，因此这里不做
"一句一事件"的细粒度抽取（src.extraction 已提供该能力/PAI 模型），而是：
1. 优先使用问题文本里给出的 Dxxx（阶段标签）提示；
2. 否则用阶段词库 + 标题/正文关键词判定事件类型；
3. 触发词取阶段标签或句中命中的因果/动作触发词；
4. mention 取正文首条有效句；主体/地点/时间/影响以规则抽取回填。

规则基线离线即可运行；如需更强的细粒度抽取，可在 PAI 模型训练后替换
build_events 内部实现，对外签名保持不变。
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..common.schemas import Argument, Document, Event

# 阶段标签词库（按优先级，命中即用）
_STAGE_LEXICON = [
    ("事故发生", ("事故发生", "突发", "发生事故", "空难", "坠毁", "爆炸", "起火",
                  "坍塌", "塌方", "泄漏", "泄露", "地震", "洪水", "暴雨", "内涝",
                  "台风", "危机", "撞击", "相撞", "遇难", "伤亡", "受灾", "感染疫情")),
    ("现场救援", ("救援", "搜救", "抢险", "抢救", "获救", "救出", "应急联动",
                  "赶赴现场", "医疗队", "消防", "绿色通道")),
    ("官方部署", ("启动应急", "部署", "成立.*指挥", "紧急会议", "召开.*会议",
                  "应急响应", "工作组.*赴", "交通管制", "下令", "批示")),
    ("原因调查", ("调查组", "事故调查", "原因.*调查", "初步认定", "查明", "勘查",
                  "调查结果", "认定.*原因", "排查.*隐患.*调查")),
    ("责任追究", ("责任追究", "追究.*责任", "问责", "立案", "强制措施", "刑事拘留",
                  "批捕", "起诉", "处罚", "责任人")),
    ("善后处置", ("善后", "安抚", "补偿", "赔偿", "抚恤", "安置", "救助", "理赔")),
    ("隐患分析", ("隐患", "违规操作", "管理漏洞", "短板", "缺陷", "薄弱环节",
                  "管理缺失", "设备故障", "操作失误")),
    ("专项整治", ("专项整治", "排查整治", "整改", "整治行动", "专项排查", "全面整改",
                  "标准修订", "加强监管", "堵塞漏洞")),
    ("行业转型", ("转型", "系统性提升", "升级", "推动.*行业", "高质量发展",
                  "产业调整", "新模式")),
    ("调查报告", ("调查报告", "报告发布", "报告公布", "调查结论")),
]

_TIME_RE = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2}")
_LOCATION_RE = re.compile(r"[一-龥]{2,5}(?:省|市|县|区|镇|乡|州|海|峡|洋)")
_ORG_RE = re.compile(r"[一-龥A-Za-z0-9]{2,12}?(?:部门|指挥部|工作组|委员会|管理局|"
                     r"交通部|运输部|应急部|政府|公司|集团|企业|武装组织?)")
_IMPACT_CUES = ("造成", "导致", "致使", "影响", "伤亡", "遇难", "损失", "暴涨",
                "短缺", "中断", "停业", "停课", "停运")
_SENT_SPLIT = re.compile(r"[。！？；\n]")

# C 档"特殊文档"：不参与主线因果链，按内容（而非固定编号）识别
# - 多阶段汇编：一篇文档复述全部事件，含 3 个以上【D00x·标签】标记
# - 矛盾来源：两版口径冲突，对应 conflicting_sources
# - 背景信息：例行演练/行业交流会等明确声明与主线无关的文档
_DIGEST_HEAD_RE = re.compile(r"【\s*([DE]\s*\d{3,4})\s*[·•・:：]\s*([^】]{2,16}?)】")
_DIGEST_TITLE_RE = re.compile(r"综合.{0,8}(报道|汇编)|多阶段汇编")
_CONFLICT_RE = re.compile(r"存在出入|尚未一致|交叉核验|相互矛盾|数据不一致|口径.{0,8}为")
_BACKGROUND_RE = re.compile(r"无直接因果关系|仅作背景参考|并无关联|并无因果")

SPECIAL_KIND_LABELS = {
    "digest": "综合汇编",
    "conflict": "矛盾来源",
    "background": "背景信息",
}
# 供关系模块跳过：这些标签的事件不参与因果建边
NONCAUSAL_EVENT_TYPES = set(SPECIAL_KIND_LABELS.values())


def special_doc_kind(doc: Document) -> Optional[str]:
    """识别汇编/矛盾/背景三类非因果文档，其余返回 None。"""
    text = doc.text or ""
    if len(_DIGEST_HEAD_RE.findall(text)) >= 3 or _DIGEST_TITLE_RE.search(doc.title or ""):
        return "digest"
    blob = f"{doc.title}\n{text}"
    if _CONFLICT_RE.search(blob):
        return "conflict"
    if _BACKGROUND_RE.search(blob):
        return "background"
    return None


def extract_digest_labels(docs: List[Document]) -> Dict[str, str]:
    """从多阶段汇编文档中解析 【D00x·阶段标签】 全量标签映射。"""
    out: Dict[str, str] = {}
    for doc in docs:
        pairs = _DIGEST_HEAD_RE.findall(doc.text or "")
        if len(pairs) < 3 and not _DIGEST_TITLE_RE.search(doc.title or ""):
            continue
        for raw_id, lab in pairs:
            eid = re.sub(r"\s+", "", raw_id).upper()
            out.setdefault(eid, lab.strip())
    return out


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(_SENT_SPLIT, text or "") if len(s.strip()) >= 6]


def guess_stage_label(doc: Document, hint: Optional[str]) -> str:
    """判定文档主事件的阶段标签。"""
    if hint:
        return hint
    blob = f"{doc.title}\n{doc.text}"
    for label, words in _STAGE_LEXICON:
        for w in words:
            if re.search(w, blob):
                return label
    return doc.title[:12] if doc.title else doc.doc_id


def _first_argument(arguments: List[Argument], role: str) -> str:
    for a in arguments:
        if a.role == role and a.value:
            return a.value
    return ""


def _assign_labels(docs: List[Document], question_hints: Dict[str, str],
                   digest_hints: Dict[str, str],
                   special: Dict[str, str]) -> Dict[str, str]:
    """全局阶段标签分配。

    赛题文档为模板化噪声文本，逐篇独立猜标签会全部落到"事故发生"。
    优先级：特殊文档固定标签 > 问题给出的标签 > 汇编文档中的标签 >
    按叙事顺序从阶段词库补未使用标签 > 词库用尽后逐篇猜测并加序号去重。
    """
    labels: Dict[str, str] = {}
    # 1. 特殊文档（汇编/矛盾/背景）
    for doc in docs:
        kind = special.get(doc.doc_id)
        if kind:
            labels[doc.doc_id] = SPECIAL_KIND_LABELS[kind]
    # 2. 问题标签 + 3. 汇编标签
    for doc in docs:
        if doc.doc_id in labels:
            continue
        hint = question_hints.get(doc.doc_id) or digest_hints.get(doc.doc_id)
        if hint:
            labels[doc.doc_id] = hint

    used = set(labels.values())
    lexicon_labels = [label for label, _ in _STAGE_LEXICON]
    extra = 1
    for doc in docs:
        if doc.doc_id in labels:
            continue
        candidate = next((lb for lb in lexicon_labels if lb not in used), None)
        if candidate is None:
            guess = guess_stage_label(doc, None)
            candidate = guess if guess not in used else f"后续事件{extra}"
            extra += 1
        labels[doc.doc_id] = candidate
        used.add(candidate)
    return labels


def build_events(docs: List[Document],
                 label_hints: Optional[Dict[str, str]] = None) -> List[Event]:
    """每篇文档构造一个主事件（id 与 doc_id 对齐）。"""
    question_hints = label_hints or {}
    digest_hints = extract_digest_labels(docs)
    special = {doc.doc_id: kind for doc in docs
               if (kind := special_doc_kind(doc))}
    assigned = _assign_labels(docs, question_hints, digest_hints, special)
    events: List[Event] = []
    for doc in docs:
        sents = _sentences(doc.text)
        body_sents = [s for s in sents if s != doc.title]
        mention = body_sents[0] if body_sents else (sents[0] if sents else doc.title)
        label = assigned[doc.doc_id]

        args: List[Argument] = []
        m = _TIME_RE.search(doc.text)
        if m:
            args.append(Argument(role="时间", value=m.group(0)))
        m = _LOCATION_RE.search(doc.text)
        if m:
            args.append(Argument(role="地点", value=m.group(0)))
        m = _ORG_RE.search(doc.text)
        if m:
            args.append(Argument(role="主体", value=m.group(0)))
        for sent in body_sents[:4]:
            if any(c in sent for c in _IMPACT_CUES):
                args.append(Argument(role="影响", value=sent[:80]))
                break

        if doc.doc_id in special:
            confidence = 0.35          # 非因果文档，仅供定位/拒答引用
        elif question_hints.get(doc.doc_id) or digest_hints.get(doc.doc_id):
            confidence = 0.7           # 问题或汇编材料锚定
        else:
            confidence = 0.55          # 纯规则猜测
        events.append(Event(
            event_id=doc.doc_id,
            doc_id=doc.doc_id,
            event_type=label,
            trigger=label,
            mention=mention,
            arguments=args,
            time=_first_argument(args, "时间"),
            location=_first_argument(args, "地点"),
            confidence=confidence,
        ))
    return events
