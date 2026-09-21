"""真实新闻因果图谱测试：河南开封/郑州暴雨（2024-07）。

事件与因果关系由以下真实报道的事实重建（边上的 evidence 为报道要点）：
- 河南开封发布暴雨红色预警，防汛应急响应提升为三级，郑州和开封部分公交停运
- 停课、停业！河南一地发布暴雨红色预警；郑州启动蓝色内涝预警
来源见脚本末尾的 SOURCES。

用法：py scripts/demo_news_henan.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.io_utils import save_events, save_graph, save_relations  # noqa: E402
from src.common.schemas import (  # noqa: E402
    CausalRelation, Event, QT_CAUSAL_TRACING, QT_COUNTERFACTUAL, QT_SITUATION_DEDUCTION, Query,
)
from src.graph import build_graph  # noqa: E402
from src.reasoning import answer_query  # noqa: E402

SOURCES = [
    "河南开封发布暴雨红色预警，防汛应急响应提升为三级！郑州和开封部分公交停运",
    "停课、停业！河南一地发布暴雨红色预警；郑州启动蓝色内涝预警",
]


def _events():
    return [
        Event(event_id="E001", doc_id="D001", event_type="灾害/事故", trigger="暴雨",
              mention="开封发布暴雨红色预警", time="2024-07", location="河南开封", confidence=0.95),
        Event(event_id="E002", doc_id="D001", event_type="政策/发布", trigger="应急响应",
              mention="防汛应急响应提升为三级", time="2024-07", location="河南开封", confidence=0.92),
        Event(event_id="E003", doc_id="D002", event_type="灾害/事故", trigger="内涝",
              mention="郑州启动蓝色内涝预警（道路积水）", time="2024-07", location="河南郑州", confidence=0.9),
        Event(event_id="E004", doc_id="D001", event_type="社会/舆情", trigger="公交停运",
              mention="郑州和开封部分公交停运", time="2024-07", location="郑州/开封", confidence=0.88),
        Event(event_id="E005", doc_id="D002", event_type="政策/发布", trigger="停课停业",
              mention="学校停课、商户停业", time="2024-07", location="河南", confidence=0.9),
        Event(event_id="E006", doc_id="D001", event_type="社会/舆情", trigger="出行受阻",
              mention="市民出行受阻", time="2024-07", location="郑州/开封", confidence=0.85),
    ]


def _relations():
    return [
        CausalRelation("R001", "E001", "E002", "causal", ["暴雨红色预警，防汛应急响应提升为三级"], 0.9),
        CausalRelation("R002", "E001", "E003", "causal", ["强降雨导致道路积水内涝"], 0.9),
        CausalRelation("R003", "E001", "E005", "causal", ["暴雨红色预警，学校停课、商户停业"], 0.88),
        CausalRelation("R004", "E002", "E004", "causal", ["防汛应急响应提升，部分公交停运"], 0.8),
        CausalRelation("R005", "E003", "E004", "enables", ["道路内涝积水，部分公交停运"], 0.82),
        CausalRelation("R006", "E003", "E006", "causal", ["道路内涝积水，市民出行受阻"], 0.86),
        CausalRelation("R007", "E004", "E006", "causal", ["公交停运，市民出行受阻"], 0.84),
    ]


def main() -> None:
    events = _events()
    relations = _relations()
    graph = build_graph(events, relations)

    save_events(events, "data/events/news_henan.jsonl")
    save_relations(relations, "data/relations/news_henan.jsonl")
    save_graph(graph, "data/graphs/news_henan.json")

    print("=" * 70)
    print("真实新闻：河南开封/郑州暴雨（2024-07）因果图谱")
    print(f"节点 {len(graph.nodes)} 个 / 边 {len(graph.edges)} 条")
    print("图结构（cause -> effect）：")
    for e in graph.edges:
        print(f"  {e.cause_event_id} -> {e.effect_event_id}  [{e.relation_type}] {e.evidence[0][:24]}")
    print("=" * 70)

    queries = [
        Query("Q1", "是什么导致了市民出行受阻？", QT_CAUSAL_TRACING),
        Query("Q2", "暴雨红色预警会导致什么？", QT_CAUSAL_TRACING),
        Query("Q3", "暴雨红色预警可能引发哪些后续？", QT_SITUATION_DEDUCTION),
        Query("Q4", "假如公交停运没有发生，市民出行受阻还会发生吗？", QT_COUNTERFACTUAL),
        Query("Q5", "假如道路内涝没有发生，市民出行受阻还会发生吗？", QT_COUNTERFACTUAL),
        Query("Q6", "假如暴雨红色预警没有发生会怎样？", QT_COUNTERFACTUAL),
    ]
    for q in queries:
        ans = answer_query(graph, q)
        print(f"\n[{q.question_type}] {q.question}")
        print(ans.answer_text)
        print(f"  证据链={ans.evidence_chain}  置信度={ans.confidence}")

    print("\n报道要点（证据来源）：")
    for s in SOURCES:
        print("  ·", s)


if __name__ == "__main__":
    main()
