"""模块2：因果关系建立（成员 B）。

对外唯一入口：extract_relations(events) -> List[CausalRelation]
实现请在本目录下的 causal_relation.py 中完成。
"""
from .causal_relation import extract_relations

__all__ = ["extract_relations"]
