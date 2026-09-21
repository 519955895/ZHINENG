"""模块3：图谱构建（成员 C）。

对外入口：
    build_graph(events, relations) -> CausalGraph
    to_networkx(graph) -> nx.DiGraph
"""
from .graph_builder import build_graph, to_networkx

__all__ = ["build_graph", "to_networkx"]
