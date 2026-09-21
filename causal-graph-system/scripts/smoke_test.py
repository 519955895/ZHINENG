"""端到端验收脚本（合并门槛）：三人代码合并后，全队一起跑这个脚本确认能串通。

用法：py scripts/smoke_test.py

它会按挑战档顺序串联三个模块 + 推理，逐段检查：
  1. 模块1 事件抽取是否已实现、能否跑通示例数据；
  2. 模块2 因果识别是否已实现、能否消费模块1的产物；
  3. 模块3 建图 + 三类推理是否已实现；
最后输出每个模块的 PASS / FAIL，任何一段 FAIL 就说明还没到可合并状态。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.io_utils import load_documents  # noqa: E402
from src.common.schemas import QT_CAUSAL_TRACING, QT_SITUATION_DEDUCTION, QT_COUNTERFACTUAL, Query  # noqa: E402
from src.extraction import extract_events  # noqa: E402
from src.relation import extract_relations  # noqa: E402
from src.graph import build_graph  # noqa: E402
from src.reasoning import answer_query  # noqa: E402

results = []


def check(name: str, fn):
    try:
        fn()
        results.append((name, True, ""))
        print(f"[PASS] {name}")
    except NotImplementedError as e:
        results.append((name, False, str(e)))
        print(f"[FAIL] {name} —— 尚未实现：{e}")
    except Exception as e:  # noqa: BLE001
        results.append((name, False, repr(e)))
        print(f"[FAIL] {name} —— 运行出错：{e!r}")


def stage_extraction():
    docs = load_documents("data/raw/news_sample.json")
    events = extract_events(docs)
    if not events:
        raise RuntimeError("抽取结果为空，请确认模块1产出了事件")
    globals()["_events"] = events


def stage_relation():
    events = globals().get("_events")
    if not events:
        raise RuntimeError("依赖模块1的产物，请先通过模块1")
    relations = extract_relations(events)
    if not relations:
        raise RuntimeError("识别结果为空，请确认模块2产出了因果对")
    globals()["_relations"] = relations


def stage_graph_and_reasoning():
    events = globals().get("_events")
    relations = globals().get("_relations")
    graph = build_graph(events, relations)
    queries = [
        Query(query_id="Q001", question="是什么导致了道路积水？", question_type=QT_CAUSAL_TRACING),
        Query(query_id="Q002", question="交通瘫痪可能引发什么？", question_type=QT_SITUATION_DEDUCTION),
        Query(query_id="Q003", question="假如暴雨没发生会怎样？", question_type=QT_COUNTERFACTUAL),
    ]
    for q in queries:
        ans = answer_query(graph, q)
        if not ans.answer_text:
            raise RuntimeError(f"{q.question_type} 返回了空答案")


if __name__ == "__main__":
    print("=== 端到端验收 ===")
    check("模块1 事件抽取", stage_extraction)
    check("模块2 因果识别", stage_relation)
    check("模块3 建图 + 三类推理", stage_graph_and_reasoning)

    failed = [r for r in results if not r[1]]
    print("\n=== 结论 ===")
    if failed:
        print(f"{len(failed)} 个模块未通过：{[r[0] for r in failed]}")
        sys.exit(1)
    print("全部通过：三个模块可合并联调。")
