"""模块2 因果关系建立：规则基线系统测试。

覆盖场景：
  T1  基本因果链（causal，forward 提示词）
  T2  四类关系类型（causal / enables / prevents / conditional）
  T3  backward 方向提示词（因为/由于）
  T4  跨文档隔离（不同 doc_id 不互相配对）
  T5  去重（同一 (cause, effect) 只产出一条）
  T6  空输入
  T7  无提示词事件不产出关系
  T8  时序排序（按 time 决定因先于果）
  T9  输出契约校验（relation_id 唯一、cause/effect 合法、evidence 非空、类型合法）
  T10 IO 闭环（save_relations -> load_relations 往返）
"""
from __future__ import annotations

import json
import os

from src.common.io_utils import load_events, save_relations, load_relations
from src.common.schemas import (
    CausalRelation,
    Event,
    RELATION_CAUSAL,
    RELATION_CONDITIONAL,
    RELATION_ENABLES,
    RELATION_PREVENTS,
)
from src.relation import extract_relations
from src.relation.cue_pattern import find_cues

VALID_TYPES = {RELATION_CAUSAL, RELATION_ENABLES, RELATION_PREVENTS, RELATION_CONDITIONAL}

SAMPLE_PATH = "data/events/events_sample.jsonl"


def _e(eid, doc, mention, time="", etype="灾害/事故", trigger=""):
    return Event(
        event_id=eid, doc_id=doc, event_type=etype, trigger=trigger,
        mention=mention, time=time, confidence=0.9,
    )


def _to_pairs(rels):
    return [(r.cause_event_id, r.effect_event_id, r.relation_type) for r in rels]


# ---------------- T1 基本因果链 ----------------
def test_t1_causal_chain():
    events = [
        _e("E1", "D1", "遭遇暴雨", "2024-07-01T08"),
        _e("E2", "D1", "暴雨导致道路积水", "2024-07-01T10"),
        _e("E3", "D1", "积水引发车辆抛锚", "2024-07-01T12"),
    ]
    rels = extract_relations(events)
    pairs = _to_pairs(rels)
    assert ("E1", "E2", RELATION_CAUSAL) in pairs
    assert ("E2", "E3", RELATION_CAUSAL) in pairs
    assert ("E1", "E3", RELATION_CAUSAL) in pairs   # 扩展配对：跨事件因果链
    assert len(rels) == 3


# ---------------- T2 四类关系类型 ----------------
def test_t2_four_relation_types():
    events = [
        _e("E1", "D1", "下雨", "t1"),
        _e("E2", "D1", "使得地面积水", "t2"),          # enables
        _e("E3", "D1", "积水导致抛锚", "t3"),          # causal
        _e("E4", "D1", "排水阻止蔓延", "t4"),          # prevents
        _e("E5", "D1", "若持续降雨则水位上涨", "t5"),  # conditional
    ]
    rels = extract_relations(events)
    type_map = {(r.cause_event_id, r.effect_event_id): r.relation_type for r in rels}
    assert type_map.get(("E1", "E2")) == RELATION_ENABLES
    assert type_map.get(("E2", "E3")) == RELATION_CAUSAL
    assert type_map.get(("E3", "E4")) == RELATION_PREVENTS
    assert type_map.get(("E4", "E5")) == RELATION_CONDITIONAL


# ---------------- T3 backward 方向 ----------------
def test_t3_backward_direction():
    events = [
        _e("E1", "D1", "因为连日暴雨", "t1"),  # backward: E1 是因
        _e("E2", "D1", "城市发生内涝", "t2"),   # E2 是果
    ]
    rels = extract_relations(events)
    pairs = _to_pairs(rels)
    assert ("E1", "E2", RELATION_CAUSAL) in pairs


# ---------------- T4 跨文档隔离 ----------------
def test_t4_cross_doc_isolation():
    events = [
        _e("E1", "D1", "暴雨导致积水", "t1"),
        _e("E2", "D2", "积水引发抛锚", "t1"),  # 不同文档，不应与 E1 配对
    ]
    rels = extract_relations(events)
    # E1 在 D1 内无前序事件（只有自己），E2 在 D2 内无前序事件
    # 各自都无法形成 forward 配对（缺少前序因）
    assert all(r.cause_event_id != "E1" or r.effect_event_id != "E2" for r in rels)


# ---------------- T5 去重 ----------------
def test_t5_dedup():
    # 构造两个事件，E2 的 mention 含两个 forward 提示词，
    # 但 (E1, E2) 对应只产出一条
    events = [
        _e("E1", "D1", "下雨", "t1"),
        _e("E2", "D1", "导致积水引发抛锚", "t2"),
    ]
    rels = extract_relations(events)
    pairs = _to_pairs(rels)
    # 只产出一条 (E1, E2) 关系，证明去重生效
    assert sum(1 for c, e, _ in pairs if c == "E1" and e == "E2") == 1
    assert len(rels) == 1


# ---------------- T6 空输入 ----------------
def test_t6_empty_input():
    assert extract_relations([]) == []


# ---------------- T7 无提示词 ----------------
def test_t7_no_cue():
    events = [
        _e("E1", "D1", "下雨了", "t1"),
        _e("E2", "D1", "地面湿了", "t2"),
    ]
    assert extract_relations(events) == []


# ---------------- T8 时序排序 ----------------
def test_t8_temporal_order():
    # 故意把时间靠后的事件放前面，验证排序后因果方向正确
    events = [
        _e("E2", "D1", "积水引发抛锚", "t2"),
        _e("E1", "D1", "暴雨导致积水", "t1"),
    ]
    rels = extract_relations(events)
    pairs = _to_pairs(rels)
    # 排序后 E1(t1) 在前，E2(t2) 在后
    # E2.mention 含"引发"（forward），所以 E1->E2
    assert ("E1", "E2", RELATION_CAUSAL) in pairs


# ---------------- T9 输出契约校验 ----------------
def test_t9_output_contract():
    events = [
        _e("E1", "D1", "暴雨导致积水", "t1"),
        _e("E2", "D1", "积水引发抛锚", "t2"),
    ]
    # 修正：E1 含"导致"需要前序事件，这里补一个无前序的因
    events = [
        _e("E0", "D1", "天气变化", "t0"),
        _e("E1", "D1", "暴雨导致积水", "t1"),
        _e("E2", "D1", "积水引发抛锚", "t2"),
    ]
    rels = extract_relations(events)
    assert len(rels) >= 2
    ids = [r.relation_id for r in rels]
    assert len(ids) == len(set(ids)), "relation_id 必须唯一"
    valid_ids = {"E0", "E1", "E2"}
    for r in rels:
        assert r.cause_event_id in valid_ids, f"cause {r.cause_event_id} 不合法"
        assert r.effect_event_id in valid_ids, f"effect {r.effect_event_id} 不合法"
        assert r.relation_type in VALID_TYPES, f"类型 {r.relation_type} 不合法"
        assert len(r.evidence) > 0, "evidence 不能为空"
        assert 0.0 <= r.confidence <= 1.0, "confidence 越界"
        assert r.relation_id.startswith("R"), "relation_id 应以 R 开头"


# ---------------- T10 IO 闭环 ----------------
def test_t10_io_roundtrip(tmp_path):
    events = [
        _e("E1", "D1", "暴雨导致积水", "t1"),
        _e("E2", "D1", "积水引发抛锚", "t2"),
    ]
    # 补前序因
    events = [_e("E0", "D1", "天气", "t0")] + events
    rels = extract_relations(events)
    out = tmp_path / "relations.jsonl"
    save_relations(rels, str(out))
    loaded = load_relations(str(out))
    assert len(loaded) == len(rels)
    for a, b in zip(rels, loaded):
        assert a.relation_id == b.relation_id
        assert a.cause_event_id == b.cause_event_id
        assert a.effect_event_id == b.effect_event_id
        assert a.relation_type == b.relation_type
        assert a.evidence == b.evidence


# ---------------- T11 样例数据端到端（14事件/3文档/四类关系/双方向）----------------
def test_t11_sample_data_end_to_end():
    assert os.path.exists(SAMPLE_PATH), f"样例数据不存在: {SAMPLE_PATH}"
    events = load_events(SAMPLE_PATH)
    assert len(events) == 14, f"应为14个事件，实际{len(events)}"
    rels = extract_relations(events)
    pairs = _to_pairs(rels)

    # ---- D001 暴雨内涝：causal + prevents ----
    assert ("E001", "E002", RELATION_CAUSAL) in pairs       # 导致
    assert ("E002", "E003", RELATION_CAUSAL) in pairs       # 引发
    assert ("E004", "E005", RELATION_PREVENTS) in pairs     # 阻止

    # ---- D002 经济政策：backward(因为) + enables + causal + conditional ----
    assert ("E010", "E006", RELATION_CAUSAL) in pairs       # 因为 (backward)
    assert ("E006", "E007", RELATION_ENABLES) in pairs      # 使得
    assert ("E007", "E008", RELATION_CAUSAL) in pairs       # 引发
    assert ("E008", "E009", RELATION_CONDITIONAL) in pairs  # 若

    # ---- D003 社会事件：backward(由于) + causal + prevents ----
    assert ("E012", "E011", RELATION_CAUSAL) in pairs       # 由于 (backward)
    assert ("E011", "E013", RELATION_CAUSAL) in pairs       # 引发
    assert ("E013", "E014", RELATION_PREVENTS) in pairs     # 防止

    # 四类关系全覆盖
    types = {r.relation_type for r in rels}
    assert types == VALID_TYPES, f"应覆盖四类关系，实际: {types}"
    # 总数：扩展配对后 25 条
    assert len(rels) == 25, f"应为25条关系，实际{len(rels)}"
    # 跨文档隔离：无 D001↔D002↔D003 之间的配对
    doc_of = {e.event_id: e.doc_id for e in events}
    for r in rels:
        assert doc_of[r.cause_event_id] == doc_of[r.effect_event_id], \
            f"跨文档配对: {r.cause_event_id}({doc_of[r.cause_event_id]}) -> {r.effect_event_id}({doc_of[r.effect_event_id]})"


# ---------------- T12 find_cues 单元（覆盖47个提示词 + 权重 + 选优）----------------
def test_t12_find_cues():
    from src.relation.cue_pattern import CAUSAL_CUES, select_best_cue

    # find_cues 返回 4 元组 (cue, type, direction, weight)
    assert find_cues("导致") == [("导致", RELATION_CAUSAL, "forward", 0.75)]
    assert find_cues("因为") == [("因为", RELATION_CAUSAL, "backward", 0.75)]
    assert find_cues("阻止") == [("阻止", RELATION_PREVENTS, "forward", 0.55)]
    assert find_cues("如果") == [("如果", RELATION_CONDITIONAL, "forward", 0.38)]
    assert find_cues("无因果") == []

    # 多提示词命中
    multi = find_cues("导致并且阻止")
    types = [c[1] for c in multi]
    assert RELATION_CAUSAL in types
    assert RELATION_PREVENTS in types

    # ---- 新增 causal forward 提示词 ----
    for cue in ["促使", "诱发", "触发", "催生", "酿成", "带来", "招致", "掀起"]:
        hits = find_cues(cue)
        assert hits and hits[0][0] == cue, f"{cue} 未命中或优先级错误"
        assert hits[0][1] == RELATION_CAUSAL
        assert hits[0][2] == "forward"
        assert 0.0 < hits[0][3] <= 1.0  # weight 合法

    # ---- 新增 enables forward 提示词 ----
    for cue in ["进而", "得以", "借此"]:
        hits = find_cues(cue)
        assert hits and hits[0][0] == cue
        assert hits[0][1] == RELATION_ENABLES

    # ---- 新增 prevents forward 提示词 ----
    for cue in ["遏制", "抑制", "杜绝", "防范", "规避", "免于", "消除"]:
        hits = find_cues(cue)
        assert hits and hits[0][0] == cue
        assert hits[0][1] == RELATION_PREVENTS

    # ---- 新增 conditional forward 提示词 ----
    for cue in ["假如", "倘若", "要是", "只要", "假使", "若是"]:
        hits = find_cues(cue)
        assert hits and hits[0][0] == cue, f"{cue} 优先级错误: {hits}"
        assert hits[0][1] == RELATION_CONDITIONAL

    # ---- 新增 causal backward 提示词 ----
    for cue in ["缘于", "源于", "鉴于", "出于"]:
        hits = find_cues(cue)
        assert hits and hits[0][0] == cue
        assert hits[0][1] == RELATION_CAUSAL
        assert hits[0][2] == "backward"

    # ---- 优先级验证：双字词优先于单字"若" ----
    hits = find_cues("倘若")
    assert hits[0][0] == "倘若", f"双字提示词应优先: {hits}"

    # ---- 总数校验 ----
    assert len(CAUSAL_CUES) == 57, f"提示词总数应为57，实际{len(CAUSAL_CUES)}"

    # ---- select_best_cue 权重选优 ----
    # "导致"(0.75) 与 "若"(0.32) 同时命中，应选权重高的"导致"
    hits = find_cues("导致若")
    best = select_best_cue(hits)
    assert best[0] == "导致", f"应选权重最高的导致，实际: {best}"
    assert best[3] == 0.75

    # 方向冲突：forward(导致 0.75) vs backward(因为 0.75)，同权重取列表前者
    hits = find_cues("导致因为")
    best = select_best_cue(hits)
    assert best[0] == "导致", f"同权重取列表顺序前者，实际: {best}"


# ---------------- T13 配置化：strict_temporal 严格时序 ----------------
def test_t13_strict_temporal_config():
    from src.common.config import Config

    # E1 时间晚于 E2，但 E2 含"导致"(forward)，正常模式下 E1->E2 会扣减但保留
    events = [
        _e("E1", "D1", "遭遇暴雨", "2024-07-01T12"),
        _e("E2", "D1", "暴雨导致道路积水", "2024-07-01T10"),
    ]
    # 默认模式：因晚于果时扣减 confidence 但仍产出
    rels_default = extract_relations(events)
    pairs_default = _to_pairs(rels_default)
    assert ("E1", "E2", RELATION_CAUSAL) in pairs_default
    assert rels_default[0].confidence < 0.75  # 被时序扣减

    # 严格模式：因晚于果直接丢弃
    cfg_strict = Config({"relation": {"strict_temporal": True}})
    rels_strict = extract_relations(events, config=cfg_strict)
    assert rels_strict == [], "严格时序模式应丢弃因晚于果的关系"

    # 调高 min_confidence 阈值过滤弱关系
    cfg_high = Config({"relation": {"min_confidence": 0.99}})
    rels_high = extract_relations(events, config=cfg_high)
    assert rels_high == [], "高阈值应过滤掉扣减后的关系"


def test_t14_load_cue_weights_from_json(tmp_path):
    """T14: 从 JSON 文件加载标定后的提示词权重，覆盖默认值。"""
    from src.relation.cue_pattern import CAUSAL_CUES, load_cue_weights

    # 记录默认权重（不硬编码，避免与 5 档权重表耦合）
    default_weights = {cue: w for cue, _, _, w in CAUSAL_CUES}
    default_daozhi = default_weights["导致"]
    default_yinfa = default_weights["引发"]

    # 写入标定权重 JSON
    weights_path = tmp_path / "cue_weights.json"
    weights_path.write_text(json.dumps({"导致": 0.95, "引发": 0.88}), encoding="utf-8")

    updated = load_cue_weights(str(weights_path))
    assert updated == 2

    # 验证权重已覆盖
    new_weights = {cue: w for cue, _, _, w in CAUSAL_CUES}
    assert new_weights["导致"] == 0.95
    assert new_weights["引发"] == 0.88
    assert new_weights["导致"] != default_daozhi
    assert new_weights["引发"] != default_yinfa
    # 未标定的提示词保持默认
    assert new_weights["造成"] == default_weights["造成"]


def test_t15_apply_feature_weights_from_json(tmp_path):
    """T15: 从 JSON 文件加载学习到的特征权重，更新 bonus 配置。"""
    from src.relation.causal_relation import (
        DEFAULT_CONFIG,
        TOTAL_BONUS_CAP,
        apply_feature_weights,
    )

    # 记录默认 bonus
    default_loc = DEFAULT_CONFIG["location_bonus"]

    # 写入特征权重 JSON
    feat_path = tmp_path / "feature_weights.json"
    feat_path.write_text(
        json.dumps({"cue_weight": 0.5, "location": 0.3, "argument": 0.15, "time_match": 0.05}),
        encoding="utf-8",
    )

    result = apply_feature_weights(str(feat_path))
    # bonus = TOTAL_BONUS_CAP × 特征权重
    assert result["location_bonus"] == round(TOTAL_BONUS_CAP * 0.3, 4)
    assert result["argument_bonus"] == round(TOTAL_BONUS_CAP * 0.15, 4)
    assert result["time_bonus"] == round(TOTAL_BONUS_CAP * 0.05, 4)
    assert DEFAULT_CONFIG["location_bonus"] != default_loc


def test_t16_ml_scorer_injection():
    """T16: 注入 ml_scorer 时，用 ML 打分覆盖规则置信度与类型。"""
    from src.relation.causal_relation import extract_relations

    events = [
        _e("E1", "D1", "暴雨导致道路积水", "2024-07-01T10"),
        _e("E2", "D1", "道路积水引发交通拥堵", "2024-07-01T11"),
    ]

    # Mock scorer：含"导致"返回 causal 高分，否则 none
    class MockScorer:
        def score(self, cause, effect):
            if "导致" in cause or "导致" in effect:
                return 0.92, "causal"
            return 0.1, "none"

    # 规则基线：产出关系
    rels_rule = extract_relations(events)
    assert len(rels_rule) > 0

    # ML 模式：置信度来自 scorer
    rels_ml = extract_relations(events, ml_scorer=MockScorer())
    assert len(rels_ml) == 1
    assert rels_ml[0].confidence == 0.92
    assert rels_ml[0].relation_type == "causal"

    # ML 判定 none 时不产出
    class NoneScorer:
        def score(self, cause, effect):
            return 0.05, "none"

    rels_none = extract_relations(events, ml_scorer=NoneScorer())
    assert rels_none == []


# ---------------- T17 sklearn 因果打分器（训练+加载+打分）----------------

def test_t17_sklearn_scorer():
    """T17: sklearn TF-IDF+LR 打分器的训练、保存、加载、打分全流程。"""
    import os
    import tempfile
    import shutil
    from src.relation.train_ml_scorer import build_dataset, train_sklearn
    from src.relation.ml_scorer import create_ml_scorer, _detect_backend, SklearnCausalScorer
    from src.common.schemas import CausalRelation

    # 构造简单事件与标注（每文档3事件，多文档保证正负例足够）
    evts = [
        _e("A1", "D1", "地震摧毁房屋", "2024-01-01T10"),
        _e("A2", "D1", "房屋倒塌伤人", "2024-01-01T10"),
        _e("A3", "D1", "天气晴朗", "2024-01-01T10"),
        _e("B1", "D2", "暴雨引发洪水", "2024-02-01T08"),
        _e("B2", "D2", "洪水淹没村庄", "2024-02-01T08"),
        _e("B3", "D2", "小鸟飞翔", "2024-02-01T08"),
        _e("C1", "D3", "台风登陆沿海", "2024-03-01T08"),
        _e("C2", "D3", "沿海巨浪滔天", "2024-03-01T08"),
        _e("C3", "D3", "阳光明媚", "2024-03-01T08"),
        _e("D_1", "D4", "火山喷发岩浆", "2024-04-01T08"),
        _e("D_2", "D4", "岩浆烧毁森林", "2024-04-01T08"),
        _e("D_3", "D4", "微风轻拂", "2024-04-01T08"),
    ]
    gold = [
        CausalRelation(relation_id="g1", cause_event_id="A1", effect_event_id="A2",
                       relation_type="causal", evidence="", confidence=1.0),
        CausalRelation(relation_id="g2", cause_event_id="B1", effect_event_id="B2",
                       relation_type="causal", evidence="", confidence=1.0),
        CausalRelation(relation_id="g3", cause_event_id="C1", effect_event_id="C2",
                       relation_type="causal", evidence="", confidence=1.0),
        CausalRelation(relation_id="g4", cause_event_id="D_1", effect_event_id="D_2",
                       relation_type="causal", evidence="", confidence=1.0),
    ]

    # 构造数据集
    pairs, labels = build_dataset(evts, gold, neg_ratio=1.0, seed=42)
    assert len(pairs) > 0
    assert 1 in labels and 0 in labels

    # 训练并保存
    tmpdir = tempfile.mkdtemp()
    try:
        result = train_sklearn(pairs, labels, tmpdir)
        assert result["backend"] == "sklearn"
        assert result["val_accuracy"] > 0

        # 检测后端
        assert _detect_backend(tmpdir) == "sklearn"

        # 加载打分器
        scorer = create_ml_scorer(tmpdir)
        assert scorer is not None
        assert isinstance(scorer, SklearnCausalScorer)

        # 因果对应得较高概率
        prob_causal, rtype = scorer.score("地震摧毁房屋", "房屋倒塌")
        prob_non, rtype_non = scorer.score("天气晴朗", "小鸟飞翔")
        assert 0.0 <= prob_causal <= 1.0
        assert rtype in ("causal", "none")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_t17b_ml_mode_all_pairs():
    """T17b: ML 模式下即使无提示词也会遍历所有事件对打分。"""
    from src.relation.causal_relation import extract_relations

    # 两个事件都不含提示词
    events = [
        _e("E1", "D1", "地震发生", "2024-07-01T10"),
        _e("E2", "D1", "房屋倒塌", "2024-07-01T11"),
    ]

    # 规则基线：无提示词 → 不产出
    rels_rule = extract_relations(events)
    assert len(rels_rule) == 0

    # ML 模式：无提示词也打分（双向打分，正向概率更高）
    class DirectionalCausal:
        def score(self, cause, effect):
            # "地震发生"->"房屋倒塌" 因果成立；反向不成立
            if cause == "地震发生" and effect == "房屋倒塌":
                return 0.8, "causal"
            return 0.2, "none"

    rels_ml = extract_relations(events, ml_scorer=DirectionalCausal())
    assert len(rels_ml) == 1
    assert rels_ml[0].cause_event_id == "E1"
    assert rels_ml[0].effect_event_id == "E2"
    assert rels_ml[0].confidence == 0.8


def test_t18_batch_mode_equivalence():
    """T18: score_batch 接口存在时自动走批量路径，结果与逐条 score 等价。"""
    from src.relation.causal_relation import extract_relations

    events = [
        _e("B1", "D1", "暴雨导致洪水", "2024-01-01T08"),
        _e("B2", "D1", "洪水淹没村庄", "2024-01-01T09"),
        _e("B3", "D1", "小鸟在歌唱", "2024-01-01T10"),
        _e("B4", "D1", "救援队到达", "2024-01-01T11"),
    ]

    class MockScorer:
        """同时实现 score 和 score_batch 的 mock，保证两者逻辑一致。"""

        def _score_one(self, cause, effect):
            if "洪水" in cause and "淹没" in effect:
                return 0.85, "causal"
            if "暴雨" in cause and "洪水" in effect:
                return 0.75, "causal"
            return 0.15, "none"

        def score(self, cause, effect):
            return self._score_one(cause, effect)

        def score_batch(self, pairs, batch_size=64):
            return [self._score_one(c, e) for c, e in pairs]

    scorer = MockScorer()

    # 有 score_batch → 走批量路径
    rels_batch = extract_relations(events, ml_scorer=scorer)
    # 无 score_batch → 走逐条路径
    class SingleOnly:
        def score(self, cause, effect):
            if "洪水" in cause and "淹没" in effect:
                return 0.85, "causal"
            if "暴雨" in cause and "洪水" in effect:
                return 0.75, "causal"
            return 0.15, "none"
    rels_single = extract_relations(events, ml_scorer=SingleOnly())

    # 结果应一致：相同的关系对、方向、置信度
    assert len(rels_batch) == len(rels_single), (
        f"批量 vs 逐条结果数不同: {len(rels_batch)} vs {len(rels_single)}"
    )
    for rb, rs in zip(rels_batch, rels_single):
        assert rb.cause_event_id == rs.cause_event_id
        assert rb.effect_event_id == rs.effect_event_id
        assert rb.relation_type == rs.relation_type
        assert rb.confidence == rs.confidence


def test_t19_batch_bidirectional():
    """T19: 批量模式下无提示词事件对的双向打分，方向选择正确。"""
    from src.relation.causal_relation import extract_relations

    events = [
        _e("C1", "D1", "地震发生", "2024-07-01T10"),
        _e("C2", "D1", "房屋倒塌", "2024-07-01T11"),
    ]

    class BiScorer:
        def score(self, cause, effect):
            if cause == "地震发生" and effect == "房屋倒塌":
                return 0.9, "causal"
            if cause == "房屋倒塌" and effect == "地震发生":
                return 0.1, "none"
            return 0.2, "none"

        def score_batch(self, pairs, batch_size=64):
            results = []
            for c, e in pairs:
                if c == "地震发生" and e == "房屋倒塌":
                    results.append((0.9, "causal"))
                elif c == "房屋倒塌" and e == "地震发生":
                    results.append((0.1, "none"))
                else:
                    results.append((0.2, "none"))
            return results

    rels = extract_relations(events, ml_scorer=BiScorer())
    assert len(rels) == 1
    assert rels[0].cause_event_id == "C1"  # 地震是因
    assert rels[0].effect_event_id == "C2"  # 房屋倒塌是果
    assert rels[0].confidence == 0.9


def test_t20_batch_empty_and_threshold():
    """T20: 批量模式下空输入返回空；阈值过滤正常工作。"""
    from src.relation.causal_relation import extract_relations

    # 空输入
    assert extract_relations([], ml_scorer=type("S", (), {
        "score": lambda self, c, e: (0.5, "causal"),
        "score_batch": lambda self, pairs, batch_size=64: [(0.5, "causal")] * len(pairs),
    })()) == []

    # 阈值过滤
    events = [
        _e("T1", "D1", "事件A", "2024-01-01T08"),
        _e("T2", "D1", "事件B", "2024-01-01T09"),
    ]

    class LowScorer:
        def score(self, cause, effect):
            return 0.2, "none"

        def score_batch(self, pairs, batch_size=64):
            return [(0.2, "none")] * len(pairs)

    # 低于阈值（0.30）→ 不产出
    rels = extract_relations(events, ml_scorer=LowScorer())
    assert len(rels) == 0

