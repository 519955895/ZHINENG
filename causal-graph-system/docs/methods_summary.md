# 三类推理方法总结：算法与引用论文

> 本文件总结「因果追溯 / 态势推演 / 反事实推理」三类推理**实际实现**的算法，并给出对应引用论文。
> 代码全部位于 `src/reasoning/`：共享原语在 `graph_algorithms.py`，三类推理分别在各同名文件。
> 教学式推导与"为什么这么设计"见 [`docs/reasoning_methods.md`](reasoning_methods.md)。

---

## 0. 总览

| 任务 | 核心算法 | 代码文件 | 主要论文 |
|------|---------|---------|---------|
| 因果追溯 | 多因果链枚举 + 必要性标注 + PageRank | `causal_tracing.py` | Pearl (2000)；Halpern & Pearl (2005)；Page et al. (1999) |
| 态势推演 | 置信度链式传播 + 可能性树 | `situation_deduction.py` | Pearl (1988)；Lauritzen & Spiegelhalter (1988)；Endsley (1995) |
| 反事实推理 | 级联消去（do 干预）+ PN/PS/PNS | `counterfactual.py` | Pearl (1999)；Balke & Pearl (1994)；Tian & Pearl (2000) |

共享图算法原语（`graph_algorithms.py`）：

| 函数 | 算法 | 说明 |
|------|------|------|
| `path_probability` | 链式连乘 | 独立性近似下的路径联合置信度 |
| `best_path` / `reach_probability` | 全简单路径枚举取最优 | `networkx.all_simple_paths` + 概率排序 |
| `cause_chains` / `effect_chains` | 多源到目标的单源最优路径 | 每个原因/后果给一条最可能链 |
| `cascade_removal` | OR 语义不动点传播 | 干预 do(A=0) 后的级联消去 |
| `necessity` / `sufficiency` / `pns` | 概率因果三元组 | PN / PS / PNS |
| `scenario_tree` | 递归前向展开 | 可能性树（所有分支） |
| `pagerank` | 加权 PageRank | 权重取边置信度 |

**符号约定**：图 `G = (V, E)`，边 `e = (u→v)` 带置信度 `conf(e) ∈ [0,1]`，事件 `v` 的原文片段为 `mention(v)`。

---

## 1. 因果追溯（causal tracing）

**问题**：给定目标事件 B，回答"什么导致了 B？"（回溯）或"B 会导致什么？"（前瞻）。

### 1.1 算法

**① 方向判定**：按问题里的提示词判断回溯/前瞻（"什么导致/为什么/的原因"→回溯；"导致/引发/后果"→前瞻）。

**② 多因果链枚举**（`cause_chains` / `effect_chains`）：

```
cause_chains(G, B):
    for n in G.nodes, n ≠ B:
        p, path = best_path(G, n → B)      # 所有简单路径中联合置信度最高者
        if path 存在: 收集 (p, path)
    按 (p 降序, 链长升序) 排序，返回每条链 + 联合置信度
```

其中 `best_path` 为：

```
best_path(G, s → t) = argmax over 所有简单路径 s→…→t  of  Π conf(e)
```

**③ 分层呈现**：
- **直接原因/后果** = 前驱/后继节点，逐条给出边置信度；
- **根本原因** = 入度为 0 的根事件；
- **必要原因标注**：对每个直接原因 n，用 §3 的 `necessity(G, n, B)` 判定；PN ≥ 0.5 标记"且为其必要原因"；
- **关键枢纽** = PageRank Top-k（见 §1.2）。

**④ 证据链** = 最强因果链沿途边的 `relation_id` 有序序列。

### 1.2 PageRank 中心性

```
PageRank（按边置信度加权）：
    π ← 均匀分布
    repeat: π ← (1-d)/N + d · A · π      # A 为按 conf 归一化的邻接转移矩阵，d=0.85
    until 收敛
返回 π 中得分最高的 k 个节点作为"关键枢纽"
```

### 1.3 引用论文

- **结构因果模型（SCM）与 do 演算**：J. Pearl, *Causality: Models, Reasoning, and Inference*, Cambridge Univ. Press, 2000（第 2 版 2009）。
- **实际因果（actual cause）定义**：J. Halpern & J. Pearl, "Causes and Explanations: A Structural-Model Approach," *British Journal for the Philosophy of Science*, 2005；J. Halpern, *Actual Causality*, MIT Press, 2016。
- **根因定位（同构问题）**：L. Lin et al., "MicroRCA: Root Cause Localization of Performance Issues in Microservices," *IWQoS*, 2020；A. Ikram et al., "Root Cause Analysis of Failures in Microservices through Causal Discovery," *NeurIPS*, 2022。
- **PageRank 中心性**：L. Page, S. Brin, R. Motwani, T. Winograd, "The PageRank Citation Ranking: Bringing Order to the Web," Stanford InfoLab, 1999。
- **图遍历/最短路**：Dijkstra / BFS-DFS 经典（`networkx.all_simple_paths`）。

---

## 2. 态势推演（situation deduction）

**问题**：给定种子事件 S，回答"S 可能引发哪些后续？"，输出**完整的可能性树**（所有分支 + 逐层概率）。

### 2.1 算法

**① 置信度链式传播**（独立性近似下的联合概率）：

```
path_probability(G, v0 → v1 → … → vk) = Π_{i=1..k} conf(v_{i-1} → v_i)
```

这是贝叶斯网**链式法则**在"每条边独立"近似下的简化形式。

**② 可能性树**（`scenario_tree`，递归前向展开所有分支）：

```
scenario_tree(G, s, max_hops):
    build(node, cum_prob, depth):
        children = []
        if depth < max_hops:
            for t in successors(node):
                children += [ build(t, cum_prob × conf(node→t), depth+1) ]
        return {node, prob: cum_prob, children}
    return build(s, 1.0, 0)
```

- 根节点 `prob = 1.0`；每层概率 = 上层概率 × 边置信度；
- **分叉处每条分支都保留**（同一事件出现在不同分支 = 不同演化路径）；
- `max_hops` 限深，`max_nodes` 限总节点数（防组合爆炸）。

**③ 最可能最终态势**：在树的所有叶子（无后继）里取 `prob` 最高者，作为"最可能收敛的局面"；证据链取 S 到该叶子端点的最优路径。

### 2.2 引用论文

- **信念传播**：J. Pearl, *Probabilistic Reasoning in Intelligent Systems*, Morgan Kaufmann, 1988。
- **概率图模型**：D. Koller & N. Friedman, *Probabilistic Graphical Models*, MIT Press, 2009。
- **精确传播（junction tree）**：S. Lauritzen & D. Spiegelhalter, "Local Computations with Probabilities on Graphical Structures," *JRSS-B*, 1988。
- **时序推演（动态贝叶斯网）**：K. Murphy, "Dynamic Bayesian Networks: Representation, Inference and Learning," PhD thesis, UC Berkeley, 2002。
- **态势感知三层模型（感知/理解/投影）**：M. Endsley, "Toward a Theory of Situation Awareness in Dynamic Systems," *Human Factors*, 1995。
- **态势评估框架（JDL）**：A. Steinberg, C. Bowman, F. White, "Revisions to the JDL Data Fusion Model," 1999。
- **事件扩散时序建模（可选扩展）**：A. Hawkes, "Spectra of Some Self-exciting and Mutually Exciting Point Processes," *Biometrika*, 1971。

---

## 3. 反事实推理（counterfactual reasoning）

**问题**：给定 A（以及可选的结果 B），回答"假如 A 没有发生，B（或其它事件）会怎样？"。

### 3.1 算法

**① 级联消去**（`cascade_removal`，干预 do(A=0) 的 OR 语义不动点传播）：

```
cascade_removal(G, A):
    alive ← { r | r 是根节点(入度=0) 且 r ≠ A }
    repeat:
        grown ← alive
        for n in G.nodes, n ∉ alive, n ≠ A:
            if 存在前驱 p ∈ alive:
                grown ← grown ∪ {n}
        if grown == alive: break
        alive ← grown
    dead ← G.nodes \ alive
    return alive, dead
```

含义：事件发生当且仅当"它是未干预的根事件，或至少有一个发生的前驱"。删掉 A 后，
只依赖 A 的下游事件会**连锁消失**，直到遇到有其它存活原因的事件为止——这正是"连带消失的节点"。

**② 概率因果三元组（PN / PS / PNS）**：

```
PS(A→B)   = reach_probability(G, A→B)          # 充分性：最可能路径联合置信度
PN(A→B)   = 1 - p*                              # 必要性：1 - 存活子图里 B 的最可能替代路径强度
             其中 p* = max over 存活根 r  of best_path(G', r→B).prob
             若 B ∈ dead 则 PN = 1.0
PNS(A→B)  = PN × PS                             # 点估计（独立性/单调性近似）
```

- **PN（Probability of Necessity）**：A 不发生则 B 不发生的概率；
- **PS（Probability of Sufficiency）**：A 发生则 B 发生的概率；
- **PNS（必要且充分）**：点估计取 `PN×PS`；严格值落在 Pearl 边界内（见 §3.2）。

**③ 输出**：有 A 时的因果路径 + 无 A 时 B 是否存活（是否随级联消失）+ 替代路径 + 连带消失/存活节点集。

### 3.2 引用论文

- **概率因果三定义（PN/PS/PNS）**：J. Pearl, "Probabilities of Causation: Three Counterfactual Interpretations and Their Identification," *Synthese*, 1999。
- **反事实概率计算（twin-network 孪生网络）**：A. Balke & J. Pearl, "Counterfactual Probabilities: Computational Methods, Bounds and Applications," *UAI*, 1994。
- **PN/PS 的边界**：J. Tian & J. Pearl, "Probabilities of Causation: Bounds and Identification," *Annals of Mathematics and AI*, 2000。
- **结构因果 / do 演算**：J. Pearl, *Causality*, 2000/2009；J. Pearl, G. Glymour, N. Jewell, *Causal Inference in Statistics: A Primer*, Wiley, 2016。
- **反事实解释（机器学习视角）**：S. Wachter, B. Mittelstadt, C. Russell, "Counterfactual Explanations without Opening the Black Box," *Harvard J. of Law & Technology*, 2018；R. Mothilal, A. Sharma, C. Tan, "Explaining Machine Learning Classifiers through Diverse Counterfactual Explanations," *FAT\**, 2020；A.-H. Karimi et al., "A Survey of Algorithmic Recourse," *ACM Computing Surveys*, 2022。

---

## 4. 关键设计说明

1. **置信度传播是"独立性近似"**：`path_probability` 直接连乘边置信度，等价于把每条因果边当成独立贝叶斯因子；完整版应在边上放条件概率表（CPT）并用信念传播（§2.2 文献）。
2. **反事实的"级联"而非"单点删边"**：`cascade_removal` 按 OR 语义迭代到不动点，避免把 A 的孤儿子节点误判为独立替代原因（否则会低估 PN）。
3. **PN/PS 从确定性图估计 → 可升级概率估计**：当前每边一个标量置信度；升级方向是 CPT + 信念传播、或 LLM 受控推演（见 `reasoning_methods.md` 的"升级路线"）。
4. **问题锚定**：`evidence_chain.find_mentioned_events` 采用"子串强匹配优先、2-gram 重合率 ≥ 0.5 兜底"的分级匹配，降低公共二字词误命中。

---

## 5. 参考文献汇总

**因果基础与图模型**
- J. Pearl, *Causality: Models, Reasoning, and Inference*, Cambridge Univ. Press, 2000/2009.
- J. Pearl, *Probabilistic Reasoning in Intelligent Systems*, Morgan Kaufmann, 1988.
- J. Pearl, G. Glymour, N. Jewell, *Causal Inference in Statistics: A Primer*, Wiley, 2016.
- J. Pearl & D. Mackenzie, *The Book of Why*, Basic Books, 2018.
- J. Pearl, "The Seven Tools of Causal Inference, with Reflections on Machine Learning," *CACM*, 2019.
- D. Koller & N. Friedman, *Probabilistic Graphical Models*, MIT Press, 2009.
- P. Spirtes, C. Glymour, R. Scheines, *Causation, Prediction, and Search*, MIT Press, 2000.

**反事实与概率因果**
- J. Pearl, "Probabilities of Causation: Three Counterfactual Interpretations and Their Identification," *Synthese*, 1999.
- A. Balke & J. Pearl, "Counterfactual Probabilities: Computational Methods, Bounds and Applications," *UAI*, 1994.
- J. Tian & J. Pearl, "Probabilities of Causation: Bounds and Identification," *Annals of Mathematics and AI*, 2000.
- J. Halpern & J. Pearl, "Causes and Explanations: A Structural-Model Approach," *BJPS*, 2005.
- J. Halpern, *Actual Causality*, MIT Press, 2016.

**传播 / 态势 / 时序**
- S. Lauritzen & D. Spiegelhalter, "Local Computations with Probabilities on Graphical Structures," *JRSS-B*, 1988.
- K. Murphy, "Dynamic Bayesian Networks," PhD thesis, UC Berkeley, 2002.
- M. Endsley, "Toward a Theory of Situation Awareness in Dynamic Systems," *Human Factors*, 1995.
- A. Steinberg, C. Bowman, F. White, "Revisions to the JDL Data Fusion Model," 1999.
- A. Hawkes, "Spectra of Some Self-exciting and Mutually Exciting Point Processes," *Biometrika*, 1971.

**根因定位 / 中心性 / 可解释性**
- L. Page, S. Brin, R. Motwani, T. Winograd, "The PageRank Citation Ranking," Stanford InfoLab, 1999.
- L. Lin et al., "MicroRCA: Root Cause Localization of Performance Issues in Microservices," *IWQoS*, 2020.
- A. Ikram et al., "Root Cause Analysis of Failures in Microservices through Causal Discovery," *NeurIPS*, 2022.
- S. Wachter, B. Mittelstadt, C. Russell, "Counterfactual Explanations without Opening the Black Box," 2018.
- R. Mothilal, A. Sharma, C. Tan, "Explaining Machine Learning Classifiers through Diverse Counterfactual Explanations," *FAT\**, 2020.
- A.-H. Karimi et al., "A Survey of Algorithmic Recourse," *ACM Computing Surveys*, 2022.
