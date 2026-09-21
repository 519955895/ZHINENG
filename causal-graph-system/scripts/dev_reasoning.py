"""推理模块独立调试脚本：演示升级后的三类推理（多跳追溯 / 概率情景树 / PN·PS·PNS 反事实）。

用法：py scripts/dev_reasoning.py
输入：data/graphs/graph_dev.json（可先用 scripts/dev_graph.py 生成）
说明：直接以"基础档"方式加载因果图，跑 6 个示例问题，覆盖三类推理的关键能力点。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.io_utils import load_graph  # noqa: E402
from src.common.schemas import QT_CAUSAL_TRACING, QT_COUNTERFACTUAL, QT_SITUATION_DEDUCTION, Query  # noqa: E402
from src.reasoning import answer_query  # noqa: E402


def main() -> None:
    graph = load_graph("data/graphs/graph_dev.json")
    print(f"载入因果图：{len(graph.nodes)} 节点 / {len(graph.edges)} 边")

    queries = [
        # 因果追溯：回溯多跳 + 必要因
        Query("Q1", "是什么导致了多起追尾事故？", QT_CAUSAL_TRACING),
        # 因果追溯：前瞻
        Query("Q2", "道路积水会导致什么？", QT_CAUSAL_TRACING),
        # 态势推演：分叉情景树（积水既→交通瘫痪 又→公交车抛锚）
        Query("Q3", "道路积水严重可能引发哪些后续？", QT_SITUATION_DEDUCTION),
        # 反事实：两事件，验证暴雨是否为追尾的必要原因
        Query("Q4", "假如暴雨没有发生，多起追尾事故还会出现吗？", QT_COUNTERFACTUAL),
        # 反事实：单事件，看删除后哪些下游受影响
        Query("Q5", "假如交通瘫痪没有发生会怎样？", QT_COUNTERFACTUAL),
    ]

    for q in queries:
        ans = answer_query(graph, q)
        print(f"\n[{q.question_type}] {q.question}")
        print(f"  -> {ans.answer_text}")
        print(f"     evidence_chain={ans.evidence_chain} conf={ans.confidence}")
        if ans.metadata:
            print(f"     metadata={ans.metadata}")


if __name__ == "__main__":
    main()
