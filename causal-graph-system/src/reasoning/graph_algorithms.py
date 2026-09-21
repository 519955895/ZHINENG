"""图算法原语（成员 C）：供三类推理共用的图计算工具。

本模块把"因果追溯 / 态势推演 / 反事实推理"背后的图算法沉淀为可复用原语，
对应推荐文献中的经典方法：

- 路径检索与可达性         —— BFS/DFS、all_simple_paths（图遍历）
- 置信度传播               —— 链式连乘，独立性近似下的联合概率（贝叶斯网链式法则简化）
- 必要性 / 充分性 / PNS    —— Pearl 的"概率因果"（probability of necessity/sufficiency）
- 中心性                   —— PageRank，识别关键枢纽事件

所有函数只依赖 networkx 的 DiGraph（由 graph_builder.to_networkx 生成），
并假设边携带属性：relation_id / relation_type / confidence / evidence。
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import networkx as nx

Node = str


def edge_confidence(G, u: Node, v: Node) -> float:
    """读取边 (u->v) 的置信度，缺失/非法时回退为 1.0。"""
    c = G.edges[u, v].get("confidence", None)
    if c is None:
        return 1.0
    try:
        c = float(c)
    except (TypeError, ValueError):
        return 1.0
    return min(max(c, 0.0), 1.0)


def path_probability(G, path: Sequence[Node]) -> float:
    """沿路径的联合置信度（链式连乘，独立性近似）。"""
    if len(path) < 2:
        return 1.0
    p = 1.0
    for a, b in zip(path, path[1:]):
        p *= edge_confidence(G, a, b)
    return p


def all_simple_paths(G, source: Node, target: Node,
                     max_depth: Optional[int] = None) -> List[List[Node]]:
    """source->target 的全部简单路径，max_depth 为最大边数（None 不限制）。"""
    cutoff = None if max_depth is None else int(max_depth)
    try:
        return list(nx.all_simple_paths(G, source, target, cutoff=cutoff))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def top_k_paths(G, source: Node, target: Node, k: int = 1,
                max_depth: Optional[int] = None) -> List[Tuple[float, List[Node]]]:
    """按路径概率降序返回 top-k 条因果链 [(prob, path), ...]。"""
    paths = all_simple_paths(G, source, target, max_depth)
    scored = sorted(((path_probability(G, p), p) for p in paths),
                    key=lambda x: x[0], reverse=True)
    return scored[:k]


def best_path(G, source: Node, target: Node,
              max_depth: Optional[int] = None) -> Optional[Tuple[float, List[Node]]]:
    scored = top_k_paths(G, source, target, k=1, max_depth=max_depth)
    return scored[0] if scored else None


def reach_probability(G, source: Node, target: Node,
                      max_depth: Optional[int] = None) -> float:
    """source 触发 target 的强度估计：取最可能路径的联合置信度。"""
    bp = best_path(G, source, target, max_depth)
    return bp[0] if bp else 0.0


def union_reach_probability(G, sources: Iterable[Node], target: Node,
                            max_depth: Optional[int] = None) -> float:
    """多个独立原因"至少其一"触发目标的概率：1 - prod(1 - p_i)。"""
    acc = 1.0
    for s in sources:
        acc *= (1.0 - reach_probability(G, s, target, max_depth))
    return 1.0 - acc


def roots(G) -> List[Node]:
    """入度为 0 的根事件节点。"""
    return [n for n in G.nodes if G.in_degree(n) == 0]


def upstream_probabilities(G, target: Node,
                           max_depth: Optional[int] = None) -> Dict[Node, float]:
    """所有上游原因节点 -> 其到 target 的最可能路径概率。"""
    out: Dict[Node, float] = {}
    for n in G.nodes:
        if n == target:
            continue
        p = reach_probability(G, n, target, max_depth)
        if p > 0:
            out[n] = p
    return out


def downstream_probabilities(G, source: Node,
                             max_depth: Optional[int] = None) -> Dict[Node, float]:
    """所有下游影响节点 -> source 到其的最可能路径概率。"""
    out: Dict[Node, float] = {}
    for n in G.nodes:
        if n == source:
            continue
        p = reach_probability(G, source, n, max_depth)
        if p > 0:
            out[n] = p
    return out


def cause_chains(G, target: Node,
                 max_depth: Optional[int] = None) -> List[Tuple[float, List[Node]]]:
    """枚举"多个原因"各自的完整因果链：每个上游节点 n 到 target 的最可能路径。

    返回按 (联合置信度降序, 链长升序) 排序的 [(prob, path), ...]，path 从原因指向 target。
    这正是"是什么导致了 X"里要列出的多条因果链：直接原因、间接原因、根原因各成一条链。
    """
    chains: List[Tuple[float, List[Node]]] = []
    for n in G.nodes:
        if n == target:
            continue
        bp = best_path(G, n, target, max_depth)
        if bp:
            chains.append((bp[0], bp[1]))
    chains.sort(key=lambda x: (-x[0], len(x[1])))
    return chains


def effect_chains(G, source: Node,
                  max_depth: Optional[int] = None) -> List[Tuple[float, List[Node]]]:
    """枚举"多个后果"各自的完整影响链：source 到每个下游节点 n 的最可能路径。

    返回按 (联合置信度降序, 链长升序) 排序的 [(prob, path), ...]，path 从 source 指向后果。
    """
    chains: List[Tuple[float, List[Node]]] = []
    for n in G.nodes:
        if n == source:
            continue
        bp = best_path(G, source, n, max_depth)
        if bp:
            chains.append((bp[0], bp[1]))
    chains.sort(key=lambda x: (-x[0], len(x[1])))
    return chains


def edge_ids(G, path: Sequence[Node]) -> List[str]:
    """路径上每条边的 relation_id 有序序列，作为证据链。"""
    return [G.edges[a, b]["relation_id"] for a, b in zip(path, path[1:])]


def cascade_removal(G, cause: Node) -> Tuple[set, set]:
    """do(cause=0) 的级联消去：把"因 cause 消失而连带消失"的节点全部找出。

    存活判定采用 OR 语义（事件发生 iff 存在至少一个发生的原因）：
    - 未干预的根事件（原图入度为 0）初始存活；
    - 非根节点存活 iff 至少一个前驱存活；
    迭代到不动点后，返回 (存活节点集合, 消失节点集合)。

    这就是反事实里"连带消失的节点"的正确传播方式：删掉 A 后，
    只依赖 A 的下游节点会一路连锁消失，直到遇到有其它存活原因的节点为止。
    """
    alive = {r for r in roots(G) if r != cause}
    while True:
        grown = set(alive)
        for n in G.nodes:
            if n == cause or n in alive:
                continue
            if any(p in alive for p in G.predecessors(n)):
                grown.add(n)
        if grown == alive:
            break
        alive = grown
    dead = set(G.nodes) - alive
    return alive, dead


def necessity(G, cause: Node, effect: Node,
              max_depth: Optional[int] = None) -> Tuple[float, List[Node]]:
    """必要性 PN 的图估计（级联语义）：do(cause=0) 后，effect 若随级联消失则 PN=1，
    否则用存活子图里"最可能的替代因果路径强度"的补数估计 PN。

    返回 (necessity, alternative_path)：
    - necessity ∈ [0,1]；=1 表示 cause 是 effect 的必要原因
      （含级联：cause 消失会连带 effect 消失）；
    - alternative_path 为 effect 仍存活时的替代因果链（若存在）。
    """
    if cause == effect or cause not in G or effect not in G:
        return 0.0, []
    alive, dead = cascade_removal(G, cause)
    if effect in dead:
        return 1.0, []
    H = G.subgraph(alive).copy()
    surviving, alt_path = 0.0, []
    for r in roots(H):
        bp = best_path(H, r, effect, max_depth)
        if bp and bp[0] > surviving:
            surviving, alt_path = bp[0], bp[1]
    return round(1.0 - surviving, 6), alt_path


def sufficiency(G, cause: Node, effect: Node,
                max_depth: Optional[int] = None) -> float:
    """充分性 PS 的图估计：cause 单独触发 effect 的最可能路径概率。"""
    return reach_probability(G, cause, effect, max_depth)


def pns(G, cause: Node, effect: Node,
        max_depth: Optional[int] = None) -> Tuple[float, float, float]:
    """概率因果三元组 (PN, PS, PNS)。

    - PN：必要性（Probability of Necessity），effect 不发生若 cause 不发生；
    - PS：充分性（Probability of Sufficiency），effect 发生若 cause 发生；
    - PNS：必要且充分（Probability of Necessity and Sufficiency），点估计取 PN*PS，
      在独立性/单调性假设下的近似；严格值落在 Pearl 边界内，详见 docs/reasoning_methods.md。
    """
    pn, _ = necessity(G, cause, effect, max_depth)
    ps = sufficiency(G, cause, effect, max_depth)
    return pn, ps, pn * ps


def pagerank(G) -> Dict[Node, float]:
    """PageRank 中心性（按边置信度加权），识别关键枢纽事件；失败时回退非加权。"""
    try:
        return nx.pagerank(G, weight="confidence")
    except Exception:  # noqa: BLE001
        try:
            return nx.pagerank(G)
        except Exception:  # noqa: BLE001
            return {n: 0.0 for n in G.nodes}


def describe_path(G, path: Sequence[Node], node_map, include_prob: bool = False) -> str:
    """把节点 id 路径转成可读文本（mention 链）。"""
    mentions = [node_map[n].mention for n in path]
    s = " -> ".join(mentions)
    if include_prob and len(path) >= 2:
        s += f"（联合置信度 {path_probability(G, path):.2f}）"
    return s


def describe_chains(G, chains, node_map, max_items: Optional[int] = None) -> List[str]:
    """把 [(prob, path), ...] 渲染成可读的链列表（每条带联合置信度）。"""
    items = []
    for prob, path in chains[:max_items]:
        items.append(f"{describe_path(G, path, node_map)}（联合置信度 {prob:.2f}）")
    return items


def scenario_tree(G, source: Node, max_hops: Optional[int] = None,
                  max_nodes: int = 500):
    """前向情景树：从 source 展开所有后继分支，得到"一棵可能性的树"。

    返回嵌套结构：{'node': id, 'prob': 累计路径概率, 'children': [ ... ]}。
    - 根节点 prob=1.0，子节点 prob = 父 prob * 边置信度；
    - 分叉处每个后继都保留（体现"可能性"），同一节点出现在不同分支即为不同路径；
    - max_hops 限深、max_nodes 限总节点数（防组合爆炸）。
    """
    if max_hops is None:
        max_hops = G.number_of_nodes()
    budget = {"n": 0}

    def build(node, cum_prob, depth):
        budget["n"] += 1
        if budget["n"] > max_nodes:
            return None
        children = []
        if depth < max_hops:
            for s in G.successors(node):
                child = build(s, cum_prob * edge_confidence(G, node, s), depth + 1)
                if child is not None:
                    children.append(child)
        return {"node": node, "prob": round(cum_prob, 4), "children": children}

    return build(source, 1.0, 0)


def render_scenario_tree(tree, node_map) -> str:
    """把 scenario_tree 的嵌套结构渲染为带分支连接线的缩进文本。"""
    out: List[str] = []

    def walk(node, prefix, is_last, is_root):
        connector = "" if is_root else ("└─ " if is_last else "├─ ")
        label = f"{node_map[node['node']].mention}（p={node['prob']:.2f}）"
        out.append(prefix + connector + label)
        children = node.get("children", [])
        child_prefix = prefix + ("" if is_root else ("   " if is_last else "│  "))
        for i, ch in enumerate(children):
            walk(ch, child_prefix, i == len(children) - 1, False)

    walk(tree, "", True, True)
    return "\n".join(out)
