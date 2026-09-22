"""论元角色识别与填充（成员 A · 模块1）。

在规则基线 time/location 之上，补全 subject/object 等论元，使 events.jsonl 达到
"下游因果识别可用"的质量（模块2 需要 subject 判断因果方向）。

实现：jieba 分词 + 词性标注 + 启发式规则
- subject：触发词左侧最近的施事名词性成分（跨功能词/标点回找，遇子句边界停）；
- object ：触发词右侧最近的受事名词性成分；
- instrument / manner：关键词正则兜底；
- result：与 object 高度重叠，规则阶段暂不抽，避免误填（留待模型）。

约束：
- 只产出通用角色（TEAM_ROLES 的 7 类）；
- jieba 为可选依赖，不可用时自动降级（不抛异常），subject/object 留空。
"""
from __future__ import annotations

import re
from typing import List, Tuple

from ..common.schemas import Argument

try:
    import jieba
    jieba.setLogLevel(40)  # 静默词典构建日志
    import jieba.posseg as pseg
    _HAS_JIEBA = True
except Exception:  # pragma: no cover - jieba 为可选依赖
    pseg = None
    _HAS_JIEBA = False

# 抽取 subject/object 时跳过的模糊量词/代词（指代消解不在规则阶段做）
_SKIP_WORDS = {
    "部分", "一些", "许多", "大量", "若干", "不少", "全部", "所有", "其他", "其它",
    "该", "这", "那", "这些", "那些", "某", "每", "各", "本", "此", "上述", "以下",
    "他", "她", "它", "他们", "她们", "它们", "我们", "你们", "其", "之",
    "一", "两", "几", "数", "多", "少", "众多", "多名", "多人", "此次", "本次",
    "时", "环比", "同比",
}

# 子句边界标点：仅句末标点作边界，逗号/顿号/冒号不阻断（受事常在逗号后）
_SENT_BOUNDARY = set("。！？；\n")

_INSTRUMENT_RE = re.compile(
    r"(?:(?<![信应通日费急军公民两])用|利用|使用|采用|通过|凭借|借助|依靠|经由)([\u4e00-\u9fa5A-Za-z0-9]{1,10})")
_MANNER_RE = re.compile(
    r"(?:以|用)([\u4e00-\u9fa5]{1,10}?)(?:的)?(?:方式|方法|手段|态度|速度|形式|途径|模式)")


def _tokenize(text: str) -> List[Tuple[str, str, int, int]]:
    """jieba 分词并带字符偏移，返回 [(word, flag, start, end)]，end 半开。"""
    if not _HAS_JIEBA:
        return []
    tokens: List[Tuple[str, str, int, int]] = []
    pos = 0
    for w in pseg.cut(text):
        word, flag = w.word, w.flag
        idx = text.find(word, pos)
        if idx == -1:
            idx = pos
        tokens.append((word, flag, idx, idx + len(word)))
        pos = idx + len(word)
    return tokens


def _is_noun(flag: str) -> bool:
    # 只认真正名词性词：n 名词、nr 人名、ns 地名、nt 机构、nz 专名等；
    # 排除 vn 名动词（如"影响/研究"）、an 名形词，避免把动作误当受事。
    return flag.startswith("n") or flag == "j"


def _is_skip(word: str) -> bool:
    return (not word) or word in _SKIP_WORDS


def _find_trigger_idx(tokens, trigger_pos: int) -> int:
    """定位触发词所在的 token 下标。"""
    for i, (_, _, s, e) in enumerate(tokens):
        if s <= trigger_pos < e:
            return i
    return -1


def _pick_noun_before(tokens, idx: int, max_span: int = 8) -> str:
    """触发词左侧最近的施事名词（跨功能词/标点回找，遇子句边界停）。"""
    for i in range(idx - 1, max(idx - 1 - max_span, -1), -1):
        w, f, _, _ = tokens[i]
        if not w:
            continue
        if w in _SENT_BOUNDARY:
            break
        if _is_skip(w) or not _is_noun(f):
            continue
        return w
    return ""


def _pick_noun_after(tokens, idx: int, max_span: int = 8) -> str:
    """触发词右侧最近的受事名词（跨功能词/标点前瞻，遇子句边界停）。"""
    for i in range(idx + 1, min(idx + 1 + max_span, len(tokens))):
        w, f, _, _ = tokens[i]
        if not w:
            continue
        if w in _SENT_BOUNDARY:
            break
        if _is_skip(w) or not _is_noun(f):
            continue
        return w
    return ""


def _extract_instrument(text: str) -> str:
    m = _INSTRUMENT_RE.search(text)
    if not m:
        return ""
    val = m.group(1).strip()
    return val if val and not re.fullmatch(r"[\d\s]+", val) else ""


def _extract_manner(text: str) -> str:
    m = _MANNER_RE.search(text)
    return m.group(1).strip() if m else ""


def extract_arguments(text: str, trigger_start: int, trigger_end: int) -> List[Argument]:
    """基于触发词位置抽取 subject/object/instrument/manner（不含 time/location）。

    time/location 由 event_extractor 用正则单独抽取，这里只负责施事/受事等。
    """
    args: List[Argument] = []

    subj = obj = ""
    tokens = _tokenize(text)
    if tokens:
        idx = _find_trigger_idx(tokens, trigger_start)
        if idx >= 0:
            subj = _pick_noun_before(tokens, idx)
            obj = _pick_noun_after(tokens, idx)

    if subj:
        args.append(Argument(role="subject", value=subj))
    if obj:
        args.append(Argument(role="object", value=obj))

    inst = _extract_instrument(text)
    if inst:
        args.append(Argument(role="instrument", value=inst))
    mann = _extract_manner(text)
    if mann:
        args.append(Argument(role="manner", value=mann))

    return args
