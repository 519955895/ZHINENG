"""证据链工具：把图上的边/节点 id 序列映射回原文证据片段，
并提供"从问题文本定位相关事件"的辅助函数。

问题锚定采用"分级匹配"以降低误命中：
- 强匹配（子串）：trigger 或 mention 作为完整片段出现在问题文本中（或反之）；
- 兜底匹配（2-gram 重合率 ≥ 阈值）：仅当没有任何强匹配时才启用，
  且要求重合率足够高，避免"预警""发生"这类公共二字词造成误命中。
"""
from __future__ import annotations

from typing import List, Optional

from ..common.schemas import CausalGraph, Event

# 2-gram 兜底匹配的最低重合率：重合数 / 较短文本的 2-gram 总数。
# 例如"暴雨红色预警"与"内涝预警"只共享 1 个 2-gram（"预警"），重合率远低于 0.5，会被拒绝。
_FALLBACK_RATIO = 0.5


def collect_evidence(graph: CausalGraph, chain_ids: List[str]) -> List[str]:
    """按 id 序列收集原文证据片段。"""
    evidence: List[str] = []
    edge_map = {e.relation_id: e for e in graph.edges}
    node_map = graph.node_map()
    for cid in chain_ids:
        if cid in edge_map:
            evidence.extend(edge_map[cid].evidence)
        elif cid in node_map:
            evidence.append(node_map[cid].mention)
    return evidence


def _is_substring(a: str, b: str) -> bool:
    """a 作为完整片段出现在 b 中，或 b 出现在 a 中。"""
    if not a or not b:
        return False
    return a in b or b in a


def _ngram_overlap_ratio(a: str, b: str, n: int = 2) -> float:
    """a、b 的字符 n-gram 重合率 = 交集数 / 较短文本的 n-gram 总数。"""
    if not a or not b:
        return 0.0
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) < n:
        return 1.0 if _is_substring(shorter, longer) else 0.0
    s = {shorter[i:i + n] for i in range(len(shorter) - n + 1)}
    l = {longer[i:i + n] for i in range(len(longer) - n + 1)}
    if not s:
        return 0.0
    return len(s & l) / len(s)


def _match_score(event: Event, text: str) -> int:
    """事件与问题文本的匹配强度：3=子串强匹配，2=2-gram 高重合兜底，0=不匹配。"""
    for frag in (event.trigger, event.mention):
        if len(frag) >= 2 and _is_substring(frag, text):
            return 3
    best = 0.0
    for frag in (event.trigger, event.mention):
        r = _ngram_overlap_ratio(frag, text)
        if r > best:
            best = r
    return 2 if best >= _FALLBACK_RATIO else 0


def find_mentioned_events(graph: CausalGraph, text: str,
                          limit: Optional[int] = None) -> List[Event]:
    """从问题文本锚定相关事件（按图中顺序、去重）。

    策略：先找子串强匹配；一旦存在强匹配，就只返回强匹配，丢弃 2-gram 兜底匹配，
    避免公共二字词（如"预警"）把无关事件拉进来。仅在完全无强匹配时才启用兜底。
    """
    strong: List[Event] = []
    weak: List[Event] = []
    seen = set()
    for n in graph.nodes:
        if n.event_id in seen:
            continue
        s = _match_score(n, text)
        if s == 3:
            strong.append(n)
            seen.add(n.event_id)
        elif s == 2:
            weak.append(n)
            seen.add(n.event_id)

    chosen = strong if strong else weak
    return chosen[:limit] if limit else chosen
