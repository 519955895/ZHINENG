"""推理模块（图算法原语 + 三类问答）的单元测试。

覆盖：置信度传播、必要性/充分性/PNS、三类问题的分发与证据链生成。
"""
import pytest

from src.common.schemas import (
    CausalGraph,
    CausalRelation,
    Event,
    QT_CAUSAL_TRACING,
    QT_COUNTERFACTUAL,
    QT_SITUATION_DEDUCTION,
    Query,
)
from src.graph import to_networkx
from src.reasoning import answer_query
from src.reasoning import graph_algorithms as ga
from src.reasoning.evidence_chain import find_mentioned_events


def _event(eid, mention):
    return Event(event_id=eid, doc_id="D0", event_type="t", trigger=mention, mention=mention)


def _rel(rid, c, e, conf=1.0, rtype="causal"):
    return CausalRelation(relation_id=rid, cause_event_id=c, effect_event_id=e,
                          relation_type=rtype, evidence=[], confidence=conf)


def _branch_graph():
    """A->B->D 与 A->C->D 两条路径汇入 D；E->F->G 单链。"""
    events = [
        _event("A", "暴雨"), _event("B", "积水"), _event("C", "排水失效"),
        _event("D", "交通瘫痪"), _event("E", "断电"), _event("F", "信号中断"),
        _event("G", "救援受阻"),
    ]
    rels = [
        _rel("R1", "A", "B", 0.9), _rel("R2", "A", "C", 0.8),
        _rel("R3", "B", "D", 0.85), _rel("R4", "C", "D", 0.7),
        _rel("R5", "E", "F", 0.9), _rel("R6", "F", "G", 0.8),
    ]
    return CausalGraph(graph_id="G", nodes=events, edges=rels)


def test_path_probability_multiplies():
    G = to_networkx(_branch_graph())
    assert ga.path_probability(G, ["A", "B", "D"]) == pytest.approx(0.9 * 0.85)


def test_best_path_prefers_stronger_chain():
    G = to_networkx(_branch_graph())
    bp = ga.best_path(G, "A", "D")
    assert bp is not None
    assert bp[1] == ["A", "B", "D"]
    assert bp[0] == pytest.approx(0.9 * 0.85)


def test_necessity_single_chain_is_necessary():
    G = to_networkx(_branch_graph())
    pn, alt = ga.necessity(G, "F", "G")
    assert pn == pytest.approx(1.0)
    assert alt == []


def test_necessity_with_alternative_path():
    G = to_networkx(_branch_graph())
    pn, alt = ga.necessity(G, "B", "D")
    # 删除 B 后，A->C->D 仍可达，剩余强度 0.8*0.7=0.56
    assert pn == pytest.approx(1.0 - 0.8 * 0.7)
    assert alt == ["A", "C", "D"]


def test_sufficiency_and_pns():
    G = to_networkx(_branch_graph())
    assert ga.sufficiency(G, "B", "D") == pytest.approx(0.85)
    pn, ps, pns = ga.pns(G, "B", "D")
    assert pn == pytest.approx(1.0 - 0.8 * 0.7)
    assert ps == pytest.approx(0.85)
    assert pns == pytest.approx(pn * ps)


def test_cascade_removal_propagates():
    G = to_networkx(_branch_graph())
    alive, dead = ga.cascade_removal(G, "A")
    assert alive == {"E", "F", "G"}
    assert dead == {"A", "B", "C", "D"}
    # 级联语义下，A 是 D 的必要原因（删 A 后 D 连带消失）
    pn, alt = ga.necessity(G, "A", "D")
    assert pn == pytest.approx(1.0)
    assert alt == []


def test_cause_chains_and_scenario_tree():
    G = to_networkx(_branch_graph())
    chains = ga.cause_chains(G, "D")
    assert len(chains) == 3  # A->B->D, B->D, C->D（每个原因一条最可能链）
    tree = ga.scenario_tree(G, "A", max_hops=3)
    assert tree["node"] == "A"
    assert len(tree["children"]) == 2
    node_map = {n: _event(n, n) for n in G.nodes}
    rendered = ga.render_scenario_tree(tree, node_map)
    assert "├─" in rendered and "└─" in rendered


def test_find_mentioned_events_prefers_substring():
    # 共享"预警"二字不应把"内涝预警"误命中为"暴雨红色预警"
    g = CausalGraph(
        graph_id="G2",
        nodes=[Event(event_id="X1", doc_id="D0", event_type="t", trigger="暴雨", mention="开封发布暴雨红色预警"),
               Event(event_id="X2", doc_id="D0", event_type="t", trigger="内涝", mention="郑州启动蓝色内涝预警（道路积水）")],
        edges=[],
    )
    hits = find_mentioned_events(g, "假如暴雨红色预警没有发生会怎样？")
    assert [h.event_id for h in hits] == ["X1"]


def test_answer_query_three_types():
    graph = _branch_graph()
    queries = [
        Query(query_id="Q1", question="是什么导致了交通瘫痪？", question_type=QT_CAUSAL_TRACING),
        Query(query_id="Q2", question="暴雨可能引发什么？", question_type=QT_SITUATION_DEDUCTION),
        Query(query_id="Q3", question="假如暴雨没有发生，交通瘫痪会怎样？", question_type=QT_COUNTERFACTUAL),
    ]
    for q in queries:
        ans = answer_query(graph, q)
        assert ans.answer_text, q.question_type
        if q.question_type == QT_COUNTERFACTUAL:
            assert ans.metadata.get("PN") is not None
            assert ans.metadata.get("PS") is not None
        else:
            assert ans.evidence_chain, q.question_type
