"""数据结构契约的往返序列化测试：保证三人之间 JSON 交接不丢字段。"""
from src.common.schemas import (
    Argument,
    CausalGraph,
    CausalRelation,
    Document,
    Event,
    Query,
    Answer,
)


def test_event_roundtrip():
    e = Event(
        event_id="E001",
        doc_id="D001",
        event_type="灾害/事故",
        trigger="发生",
        mention="郑州市遭遇强暴雨",
        arguments=[Argument(role="location", value="郑州市")],
        time="2024-07-01",
        location="郑州市",
        char_offset=(0, 9),
        confidence=0.93,
    )
    e2 = Event.from_dict(e.to_dict())
    assert e == e2
    assert e2.get_arg("location") == "郑州市"


def test_relation_roundtrip():
    r = CausalRelation(
        relation_id="R001",
        cause_event_id="E001",
        effect_event_id="E002",
        relation_type="causal",
        evidence=["暴雨导致道路积水"],
        confidence=0.88,
    )
    assert CausalRelation.from_dict(r.to_dict()) == r


def test_graph_roundtrip():
    g = CausalGraph(
        graph_id="G001",
        nodes=[Event(event_id="E001", doc_id="D001", event_type="t", trigger="x", mention="m")],
        edges=[CausalRelation(relation_id="R001", cause_event_id="E001", effect_event_id="E002")],
    )
    g2 = CausalGraph.from_dict(g.to_dict())
    assert g2.graph_id == "G001"
    assert len(g2.nodes) == 1 and len(g2.edges) == 1


def test_query_answer_roundtrip():
    q = Query(query_id="Q001", question="什么导致积水？", question_type="causal_tracing")
    a = Answer(query_id="Q001", question_type="causal_tracing",
               answer_text="暴雨导致积水", evidence_chain=["R001"])
    assert Query.from_dict(q.to_dict()) == q
    assert Answer.from_dict(a.to_dict()) == a


def test_document_roundtrip():
    d = Document(doc_id="D001", title="t", text="正文")
    assert Document.from_dict(d.to_dict()) == d
