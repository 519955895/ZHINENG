"""因果提示词与规则模式匹配（模块2 规则基线）。

把因果提示词按语义分成两类方向：
  - forward  : 提示词所在事件是"果"，其前序事件是"因"（如"导致/引发"）
  - backward : 提示词所在事件是"因"，其后序事件是"果"（如"因为/由于"）

每条提示词映射到 schemas.py 中定义的四类 relation_type：
  causal       直接因果
  enables      使能（提供条件/使成为可能）
  prevents     抑制（阻止/防止）
  conditional  条件（若…则…）

权重(weight)设计（5 档，弱提示词压到 0.4 以下避免"命中即高分"）：
  0.75  强提示词（明确因果：导致/引起/造成/引发/致使/因为/由于）
  0.55  中强提示词（较明确：促使/诱发/触发/酿成/阻止/防止）
  0.45  中等提示词（中等明确：使得/从而/避免/遏制/抑制/杜绝）
  0.38  弱提示词（语义较弱：带来/推动/衍生/防范/规避 等，以及条件类）
  0.32  极弱提示词（单字"若"，不确定性最高）

排序说明：列表顺序即同权重下的优先级，更明确的词排前面。
"""
from __future__ import annotations

from typing import List, Tuple

from ..common.schemas import (
    RELATION_CAUSAL,
    RELATION_CONDITIONAL,
    RELATION_ENABLES,
    RELATION_PREVENTS,
)

# (提示词, 关系类型, 方向, 权重)
#   forward  -> 当前事件为 effect，前一事件为 cause
#   backward -> 当前事件为 cause，后一事件为 effect
CAUSAL_CUES: List[Tuple[str, str, str, float]] = [
    # ============ 直接因果 causal (forward) ============
    ("导致", RELATION_CAUSAL, "forward", 0.75),
    ("引起", RELATION_CAUSAL, "forward", 0.75),
    ("造成", RELATION_CAUSAL, "forward", 0.75),
    ("引发", RELATION_CAUSAL, "forward", 0.75),
    ("致使", RELATION_CAUSAL, "forward", 0.75),
    ("促使", RELATION_CAUSAL, "forward", 0.55),
    ("促成", RELATION_CAUSAL, "forward", 0.55),
    ("诱发", RELATION_CAUSAL, "forward", 0.55),
    ("激起", RELATION_CAUSAL, "forward", 0.55),
    ("触发", RELATION_CAUSAL, "forward", 0.55),
    ("催生", RELATION_CAUSAL, "forward", 0.55),
    ("酿成", RELATION_CAUSAL, "forward", 0.55),
    ("以致", RELATION_CAUSAL, "forward", 0.55),
    ("以至", RELATION_CAUSAL, "forward", 0.55),
    ("故而", RELATION_CAUSAL, "forward", 0.45),
    ("是以", RELATION_CAUSAL, "forward", 0.45),
    ("因此", RELATION_CAUSAL, "forward", 0.55),
    ("带来", RELATION_CAUSAL, "forward", 0.38),
    ("招致", RELATION_CAUSAL, "forward", 0.38),
    ("衍生", RELATION_CAUSAL, "forward", 0.38),
    ("掀起", RELATION_CAUSAL, "forward", 0.38),
    ("推动", RELATION_CAUSAL, "forward", 0.38),

    # ============ 使能 enables (forward) ============
    ("使得", RELATION_ENABLES, "forward", 0.45),
    ("令", RELATION_ENABLES, "forward", 0.45),
    ("从而", RELATION_ENABLES, "forward", 0.45),
    ("进而", RELATION_ENABLES, "forward", 0.38),
    ("得以", RELATION_ENABLES, "forward", 0.38),
    ("借此", RELATION_ENABLES, "forward", 0.38),
    ("以便", RELATION_ENABLES, "forward", 0.38),

    # ============ 抑制 prevents (forward) ============
    ("阻止", RELATION_PREVENTS, "forward", 0.55),
    ("防止", RELATION_PREVENTS, "forward", 0.55),
    ("防备", RELATION_PREVENTS, "forward", 0.45),
    ("避免", RELATION_PREVENTS, "forward", 0.45),
    ("遏制", RELATION_PREVENTS, "forward", 0.45),
    ("抑制", RELATION_PREVENTS, "forward", 0.45),
    ("杜绝", RELATION_PREVENTS, "forward", 0.45),
    ("防范", RELATION_PREVENTS, "forward", 0.38),
    ("规避", RELATION_PREVENTS, "forward", 0.38),
    ("免于", RELATION_PREVENTS, "forward", 0.38),
    ("消除", RELATION_PREVENTS, "forward", 0.38),

    # ============ 条件 conditional (forward) ============
    ("如果", RELATION_CONDITIONAL, "forward", 0.38),
    ("假如", RELATION_CONDITIONAL, "forward", 0.38),
    ("倘若", RELATION_CONDITIONAL, "forward", 0.38),
    ("一旦", RELATION_CONDITIONAL, "forward", 0.38),
    ("要是", RELATION_CONDITIONAL, "forward", 0.38),
    ("只要", RELATION_CONDITIONAL, "forward", 0.38),
    ("假使", RELATION_CONDITIONAL, "forward", 0.38),
    ("若是", RELATION_CONDITIONAL, "forward", 0.38),
    ("万一", RELATION_CONDITIONAL, "forward", 0.32),
    ("若非", RELATION_CONDITIONAL, "forward", 0.32),
    ("若", RELATION_CONDITIONAL, "forward", 0.32),  # 单字，置后降低优先级与权重

    # ============ 原因在前 causal (backward) ============
    ("因为", RELATION_CAUSAL, "backward", 0.75),
    ("由于", RELATION_CAUSAL, "backward", 0.75),
    ("缘于", RELATION_CAUSAL, "backward", 0.45),
    ("源于", RELATION_CAUSAL, "backward", 0.45),
    ("鉴于", RELATION_CAUSAL, "backward", 0.45),
    ("出于", RELATION_CAUSAL, "backward", 0.45),
]


def find_cues(text: str) -> List[Tuple[str, str, str, float]]:
    """在文本中查找命中的因果提示词。

    采用最长匹配优先：若短提示词是某已命中长提示词的子串，则跳过短提示词
    （例如命中"因为"时不再单独匹配"因"）。

    Returns:
        [(cue_word, relation_type, direction, weight), ...]，
        按在 CAUSAL_CUES 中定义的顺序返回。
    """
    all_cues = [cue for cue, _, _, _ in CAUSAL_CUES]
    hits: List[Tuple[str, str, str, float]] = []
    for cue, rtype, direction, weight in CAUSAL_CUES:
        if cue in text:
            # 最长匹配：检查是否有更长的提示词也命中且包含当前提示词
            is_subsumed = False
            for longer in all_cues:
                if len(longer) > len(cue) and cue in longer and longer in text:
                    is_subsumed = True
                    break
            if not is_subsumed:
                hits.append((cue, rtype, direction, weight))
    return hits


def select_best_cue(
    hits: List[Tuple[str, str, str, float]],
) -> Tuple[str, str, str, float]:
    """从多个命中提示词中选出最优（权重最高，同权重取列表顺序第一个）。

    Returns:
        (cue_word, relation_type, direction, weight)
    """
    if not hits:
        raise ValueError("hits 不能为空")
    return max(hits, key=lambda x: x[3])


def load_cue_weights(path: str) -> int:
    """从 JSON 文件加载标定后的提示词权重，覆盖 CAUSAL_CUES 中的默认值。

    JSON 格式：{"导致": 0.82, "引发": 0.78, ...}
    未在 JSON 中出现的提示词保持默认权重。

    Returns:
        实际更新的提示词数量。
    """
    import json

    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    updated = 0
    for i, (cue, rtype, direction, _) in enumerate(CAUSAL_CUES):
        if cue in loaded:
            w = float(loaded[cue])
            CAUSAL_CUES[i] = (cue, rtype, direction, w)
            updated += 1
    return updated
