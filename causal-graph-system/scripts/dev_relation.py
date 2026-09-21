"""成员 B 独立调试脚本：不依赖 A 的真实输出，用示例事件列表验证因果识别。

用法：py scripts/dev_relation.py
说明：用 data/events/events_sample.jsonl 作输入，产出 data/relations/relations_dev.jsonl。
      等 A 实现后，把输入路径改成 data/events/events_dev.jsonl 即可联调。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.io_utils import load_events, save_relations  # noqa: E402
from src.relation import extract_relations  # noqa: E402


def main() -> None:
    events = load_events("data/events/events_sample.jsonl")
    print(f"载入 {len(events)} 个事件")

    try:
        relations = extract_relations(events)
    except NotImplementedError:
        print("[模块2 未实现] 请在 src/relation/causal_relation.py 中实现 extract_relations")
        return

    save_relations(relations, "data/relations/relations_dev.jsonl")
    print(f"识别到 {len(relations)} 条因果关系 -> data/relations/relations_dev.jsonl")
    for r in relations[:10]:
        print(f"  {r.relation_id} | {r.cause_event_id} --{r.relation_type}--> {r.effect_event_id} | conf={r.confidence}")


if __name__ == "__main__":
    main()
