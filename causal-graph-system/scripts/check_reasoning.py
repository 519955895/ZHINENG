"""推理模块的独立校验脚本（不依赖 pytest，可在受限环境直接跑）。

用法：py scripts/check_reasoning.py
覆盖：置信度传播、最优路径、必要性/充分性/PNS、三类问答的返回与证据链。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.schemas import (  # noqa: E402
    CausalGraph, CausalRelation, Event,
    QT_CAUSAL_TRACING, QT_COUNTERFACTUAL, QT_SITUATION_DEDUCTION, Query,
)
from src.graph import to_networkx  # noqa: E402
from src.reasoning import answer_query  # noqa: E402
from src.reasoning import graph_algorithms as ga  # noqa: E402
from src.reasoning.evidence_chain import find_mentioned_events  # noqa: E402


def _event(eid, mention):
    return Event(event_id=eid, doc_id="D0", event_type="t", trigger=mention, mention=mention)


def _rel(rid, c, e, conf=1.0, rtype="causal"):
    return CausalRelation(relation_id=rid, cause_event_id=c, effect_event_id=e,
                          relation_type=rtype, evidence=[], confidence=conf)


def _branch_graph():
    events = [_event("A", "暴雨"), _event("B", "积水"), _event("C", "排水失效"),
              _event("D", "交通瘫痪"), _event("E", "断电"), _event("F", "信号中断"),
              _event("G", "救援受阻")]
    rels = [_rel("R1", "A", "B", 0.9), _rel("R2", "A", "C", 0.8),
            _rel("R3", "B", "D", 0.85), _rel("R4", "C", "D", 0.7),
            _rel("R5", "E", "F", 0.9), _rel("R6", "F", "G", 0.8)]
    return CausalGraph(graph_id="G", nodes=events, edges=rels)


def approx(a, b, eps=1e-6):
    assert math.isclose(a, b, rel_tol=0, abs_tol=eps), f"{a} != {b}"


def run():
    G = to_networkx(_branch_graph())

    approx(ga.path_probability(G, ["A", "B", "D"]), 0.9 * 0.85)

    bp = ga.best_path(G, "A", "D")
    assert bp is not None and bp[1] == ["A", "B", "D"]
    approx(bp[0], 0.9 * 0.85)

    pn, alt = ga.necessity(G, "F", "G")
    approx(pn, 1.0)
    assert alt == []

    pn, alt = ga.necessity(G, "B", "D")
    approx(pn, 1.0 - 0.8 * 0.7)
    assert alt == ["A", "C", "D"]

    approx(ga.sufficiency(G, "B", "D"), 0.85)
    pn, ps, pns = ga.pns(G, "B", "D")
    approx(pn, 1.0 - 0.8 * 0.7)
    approx(ps, 0.85)
    approx(pns, pn * ps)

    # 级联消去：删 A 后 B、C、D 连带消失，E/F/G 存活
    alive, dead = ga.cascade_removal(G, "A")
    assert alive == {"E", "F", "G"}, alive
    assert dead == {"A", "B", "C", "D"}, dead
    pn, alt = ga.necessity(G, "A", "D")
    approx(pn, 1.0)
    assert alt == []

    # 情景树：A 分叉为 B、C，B 再指向 D
    tree = ga.scenario_tree(G, "A", max_hops=3)
    assert tree["node"] == "A" and len(tree["children"]) == 2
    rendered = ga.render_scenario_tree(tree, {n: type("E", (), {"mention": n})() for n in G.nodes})
    assert "├─" in rendered and "└─" in rendered

    # 因果链枚举：D 有 3 个原因节点（A、B、C），每个原因一条最可能链
    chains = ga.cause_chains(G, "D")
    assert len(chains) == 3, len(chains)

    # 问题锚定：共享"预警"二字不应把"内涝预警"误命中为"暴雨红色预警"
    g2 = CausalGraph(
        graph_id="G2",
        nodes=[Event(event_id="X1", doc_id="D0", event_type="t", trigger="暴雨", mention="开封发布暴雨红色预警"),
               Event(event_id="X2", doc_id="D0", event_type="t", trigger="内涝", mention="郑州启动蓝色内涝预警（道路积水）")],
        edges=[],
    )
    hits = find_mentioned_events(g2, "假如暴雨红色预警没有发生会怎样？")
    assert [h.event_id for h in hits] == ["X1"], [h.event_id for h in hits]

    graph = _branch_graph()
    queries = [
        Query("Q1", "是什么导致了交通瘫痪？", QT_CAUSAL_TRACING),
        Query("Q2", "暴雨可能引发什么？", QT_SITUATION_DEDUCTION),
        Query("Q3", "假如暴雨没有发生，交通瘫痪会怎样？", QT_COUNTERFACTUAL),
    ]
    for q in queries:
        ans = answer_query(graph, q)
        assert ans.answer_text, q.question_type
        if q.question_type == QT_COUNTERFACTUAL:
            assert ans.metadata.get("PN") is not None
            assert ans.metadata.get("PS") is not None
        else:
            assert ans.evidence_chain, q.question_type

    print("全部校验通过：图算法原语 + 三类推理均正常。")


if __name__ == "__main__":
    run()
