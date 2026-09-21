"""成员 C 独立调试脚本：不依赖 A/B 的真实输出，用示例事件+关系验证建图与推理。

用法：py scripts/dev_graph.py
说明：用 data/events/events_sample.jsonl + data/relations/relations_sample.jsonl 作输入，
      产出 data/graphs/graph_dev.json 并跑一遍示例问题。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.io_utils import load_events, load_relations, save_graph  # noqa: E402
from src.common.schemas import Query, QT_CAUSAL_TRACING, QT_SITUATION_DEDUCTION, QT_COUNTERFACTUAL  # noqa: E402
from src.graph import build_graph  # noqa: E402
from src.reasoning import answer_query  # noqa: E402


def main() -> None:
    events = load_events("data/events/events_sample.jsonl")
    relations = load_relations("data/relations/relations_sample.jsonl")
    print(f"载入 {len(events)} 个事件、{len(relations)} 条关系")

    try:
        graph = build_graph(events, relations)
    except NotImplementedError:
        print("[模块3 建图未实现] 请在 src/graph/graph_builder.py 中实现 build_graph")
        return

    save_graph(graph, "data/graphs/graph_dev.json")
    print(f"建图完成：{len(graph.nodes)} 节点 / {len(graph.edges)} 边 -> data/graphs/graph_dev.json")

    # 用示例问题跑一遍推理
    queries = [
        Query(query_id="Q001", question="是什么导致了道路积水严重？", question_type=QT_CAUSAL_TRACING),
        Query(query_id="Q002", question="交通瘫痪可能引发什么？", question_type=QT_SITUATION_DEDUCTION),
        Query(query_id="Q003", question="假如暴雨没有发生，追尾事故还会出现吗？", question_type=QT_COUNTERFACTUAL),
    ]
    for q in queries:
        ans = answer_query(graph, q)
        print(f"\n[{q.question_type}] {q.question}")
        print(f"  -> {ans.answer_text}")
        print(f"  evidence_chain={ans.evidence_chain} conf={ans.confidence}")


if __name__ == "__main__":
    main()
