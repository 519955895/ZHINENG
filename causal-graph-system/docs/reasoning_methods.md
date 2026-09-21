# 因果图谱三类推理：论文、方法与框架实现

> 本文件回答一个问题：**给定一张因果图谱，如何做「因果追溯 / 态势推演 / 反事实推理」？**
> 每个小节先以苏格拉底式追问逼出"真正要回答的是什么"，再给方法与文献，最后落到
> `src/reasoning/` 里的具体实现。代码入口统一为 `reasoning.answer_query(graph, query, config) -> Answer`。
>
> **只要"算法 + 引用论文"的精简版见 [`docs/methods_summary.md`](methods_summary.md)。**

---

## 0. 先问一个总问题：这三道题在"因果的哪个层级"？

**追问：** 当你说"A 导致了 B"时，你其实可以断言三件越来越强的事：

1. 只是"它们总是一起出现"（相关，association）；
2. "如果我**主动让** A 发生，B 就会发生"（干预，intervention）；
3. "如果当初 A **没有**发生，B 就不会发生"（反事实，counterfactual）。

Pearl 把这叫做**因果的三阶层级（Ladder of Causation）**。有趣的是，赛题的三类问题正好各占一层：

| 赛题任务 | 它在因果层级里的位置 | 要回答的本质问题 |
|---------|--------------------|----------------|
| 因果追溯 | 关联/干预层 | "B 的**原因链**是什么？谁在驱动它？" |
| 态势推演 | 干预层 | "对 X 做干预（X 发生）之后，**接下来**会怎样？" |
| 反事实推理 | 反事实层 | "**假如 X 没有发生**，B 还会发生吗？" |

**落地：** 框架里三类问题由 `src/reasoning/__init__.py` 的 `answer_query` 按 `question_type` 分发，
但它们共享同一套图算法原语 `src/reasoning/graph_algorithms.py`，因此"层级"的差异只体现在调用方式上。

**核心文献：**
- J. Pearl, *Causality: Models, Reasoning, and Inference*, Cambridge Univ. Press, 2000（第 2 版 2009）。
- J. Pearl, M. Glymour, N. Jewell, *Causal Inference in Statistics: A Primer*, Wiley, 2016。
- J. Pearl, "The Seven Tools of Causal Inference, with Reflections on Machine Learning," *Communications of the ACM*, 2019。

---

## 1. 因果追溯（causal tracing）

### 苏格拉底式追问

- **问：** "是什么导致了道路积水？"——你要的是"暴雨"这一个**直接原因**，还是"暴雨 → 降雨云团 → 大气环流"这条**根本原因链**？多长的链才算"原因"？
- **问：** 如果积水有"暴雨"和"排水系统失效"两个直接原因，你能说"暴雨导致了积水"吗？——这句话其实在断言**暴雨是积水的必要原因**（没有暴雨，积水就不会发生）。你验证过这个断言吗？
- **问：** 一张大图里，有些节点是"枢纽"（很多事件都经过它）。追溯时，是列出一堆原因，还是先指出**最关键的枢纽**？

### 方法

1. **多条因果链（每个原因一条完整链）**：枚举目标事件的所有上游原因节点，每个原因给出到目标的一条最可能链（直接原因 1 跳、间接原因多跳、根原因最长），按联合置信度排序。
2. **区分直接原因 vs 根本原因**：直接原因 = 前驱节点；根本原因 = 入度为 0 的**根事件**。
3. **必要原因标注（PN）**：对每个直接原因，用级联消去（见第 3 节）判断它是否为目标事件的必要原因。
4. **关键枢纽识别**：用 PageRank 中心性标出"牵一发动全身"的中间事件。

### 文献

- J. Halpern & J. Pearl, "Causes and Explanations: A Structural-Model Approach," *British Journal for the Philosophy of Science*, 2005 —— 定义"实际原因（actual cause）"，正是追溯要回答的"到底谁算原因"。
- J. Halpern, *Actual Causality*, MIT Press, 2016。
- 微服务根因定位（同构问题：在依赖/调用图里找根因）：
  - L. Lin et al., "MicroRCA: Root Cause Localization of Performance Issues in Microservices," *IWQoS*, 2020。
  - A. Ikram et al., "Root Cause Analysis of Failures in Microservices through Causal Discovery," *NeurIPS*, 2022。
  - "CausalRCA" 系列（基于因果推理的根因定位，arXiv 2022）——见文末检索链接。

### 框架落地

- `src/reasoning/causal_tracing.py`：`answer_causal_tracing(graph, query, config)`。
- 依赖原语：`graph_algorithms.cause_chains` / `effect_chains` / `necessity` / `pagerank`。
- 证据链 = 最优因果路径上的边 `relation_id` 有序序列。

---

## 2. 态势推演（situation deduction）

### 苏格拉底式追问

- **问：** 如果一个事件同时指向两个后续（分叉），"接下来会发生什么"是一个**确定答案**，还是一棵**可能性的树**？
- **问：** 你说"交通瘫痪 → 市民出行受阻"，这句话的可信度是多少？如果中间隔着三跳，每一跳都只有 0.8 的置信度，你还敢说"接下来一定会受阻"吗？——这逼出**置信度沿链传播**的必要性。
- **问：** 推演到第几跳就该停？跳数越多越"远"，但也越不可信。你的停止条件是什么？

### 方法

1. **前向多跳传播**：从种子事件沿因果边 BFS/DFS 展开，得到可达下游集合。
2. **概率传播（链式法则简化）**：一条路径的联合置信度 = 沿途边置信度的连乘 `Π p(e)`。这本质是贝叶斯网在"独立性近似"下的链式传播。
3. **可能性树（scenario tree，完整分支）**：从种子事件展开**所有后继分支**，每层概率 = 上层概率 × 边置信度；分叉处每条分支都保留，得到一棵完整的"可能态势树"。
4. **最终态势**：把出度为 0 的末端事件按强度排序，回答"最可能收敛到什么局面"。
5. **进阶（可选）**：升级为完整贝叶斯网信念传播 / 动态贝叶斯网（加时间片）/ Hawkes 过程（给每条边加时间强度）。

### 文献

- J. Pearl, *Probabilistic Reasoning in Intelligent Systems*, Morgan Kaufmann, 1988 —— 信念传播的经典。
- D. Koller & N. Friedman, *Probabilistic Graphical Models*, MIT Press, 2009。
- S. Lauritzen & D. Spiegelhalter, "Local Computations with Probabilities on Graphical Structures," *JRSS-B*, 1988 —— junction tree / 精确传播。
- K. Murphy, "Dynamic Bayesian Networks: Representation, Inference and Learning," PhD thesis, UC Berkeley, 2002 —— 时序推演。
- M. Endsley, "Toward a Theory of Situation Awareness in Dynamic Systems," *Human Factors*, 1995 —— 态势感知三层模型，其中"投影（projection）"层正是态势推演。
- A. Steinberg, C. Bowman, F. White, "Revisions to the JDL Data Fusion Model," 1999 —— 态势评估的经典框架。
- A. Hawkes, "Spectra of Some Self-exciting and Mutually Exciting Point Processes," *Biometrika*, 1971 —— 事件"传染/扩散"的时序建模。

### 框架落地

- `src/reasoning/situation_deduction.py`：`answer_situation_deduction(graph, query, config)`。
- 依赖原语：`graph_algorithms.scenario_tree` / `render_scenario_tree` / `best_path`。
- 配置：`reasoning.situation_deduction.max_hops`（最大推演深度）。
- 树的嵌套结构同时写入 `Answer.metadata["tree"]`，便于前端可视化渲染。

---

## 3. 反事实推理（counterfactual reasoning）

### 苏格拉底式追问（最关键的一节）

- **问：** "假如暴雨没有发生，追尾事故还会出现吗？"——这句话到底在问什么？请二选一：
  - (a) **只要有暴雨，就一定有追尾**？（充分性，sufficiency）
  - (b) **只要没有暴雨，就一定没有追尾**？（必要性，necessity）
  - 还是 (c) **两者都要**（必要且充分）？
- **问：** 如果追尾事故除了暴雨，还有"司机疲劳驾驶"这条独立原因，那"没有暴雨"并不能阻止追尾。你删掉暴雨后，追尾在图上**还有没有别的路径可达**？
- **问：** 反事实不是"删掉一个节点"这么简单——删掉暴雨后，它的下游"道路积水"也跟着没了，这些**连带消失**的节点你考虑了吗？

### 方法

1. **干预 + 级联消去（do(A=0) 传播）**：反事实"若 A 未发生"不只是一次删点，而是按 OR 语义级联传播——节点存活 iff 它是未干预的根事件、或至少一个前驱存活；迭代到不动点，把"只依赖 A、随 A 消失而连带消失"的节点全部找出（`cascade_removal`）。
2. **概率因果三元组（PN / PS / PNS）**：
   - **PN（必要性）**：A 不发生则 B 不发生的概率。级联消去后 B 若消失则 PN=1；否则 `PN = 1 - 存活子图里 B 的最可能替代路径强度`。
   - **PS（充分性）**：A 发生则 B 发生的概率。图上用"A 到 B 的最可能路径联合置信度"估计。
   - **PNS（必要且充分）**：点估计取 `PN × PS`（独立性/单调性假设下的近似）；严格值落在 Pearl 边界内。
3. **连带消失与替代路径显式给出**：输出连带消失节点集、B 是否存活、以及 B 存活时的替代因果链作为证据。
4. **进阶（可选）**：twin-network 精确反事实（双网络）、LLM 受控反事实推演（用图证据约束生成）。

> **为什么"删一个节点"不够？** 反事实的正确语义是**级联传播**：删掉暴雨后，只依赖它的"道路积水"也应跟着消失，
> 进而"交通瘫痪""追尾事故"一路消失。若只删暴雨而把"道路积水"误当独立原因，就会把必要性 PN 从 1.0 低估到 0.4。
> 框架里 `graph_algorithms.cascade_removal` + `necessity` 已按 OR 语义做不动点传播，正确处理了连带消失。

### 文献

- J. Pearl, "Probabilities of Causation: Three Counterfactual Interpretations and Their Identification," *Synthese*, 1999 —— PN/PS/PNS 的定义与可识别性。
- A. Balke & J. Pearl, "Counterfactual Probabilities: Computational Methods, Bounds and Applications," *UAI*, 1994 —— twin-network（孪生网络）反事实计算。
- J. Tian & J. Pearl, "Probabilities of Causation: Bounds and Identification," *Annals of Mathematics and AI*, 2000 —— PN/PS 的边界。
- 反事实解释（机器学习视角，把"反事实"当可解释工具）：
  - S. Wachter, B. Mittelstadt, C. Russell, "Counterfactual Explanations without Opening the Black Box," *Harvard J. of Law & Technology*, 2018。
  - R. Mothilal, A. Sharma, C. Tan, "Explaining Machine Learning Classifiers through Diverse Counterfactual Explanations," *FAT* , 2020。
  - A.-H. Karimi et al., "A Survey of Algorithmic Recourse," *ACM Computing Surveys*, 2022。

### 框架落地

- `src/reasoning/counterfactual.py`：`answer_counterfactual(graph, query, config)`。
- 依赖原语：`graph_algorithms.cascade_removal` / `necessity` / `sufficiency` / `pns`。
- 结果写入 `Answer.metadata` 的 `PN` / `PS` / `PNS`、`cascaded_ids`（连带消失节点）、`alive_ids`（存活节点）字段，便于评测与可视化。

---

## 4. 如何在框架内继续"升级"（可插拔设计）

契约保持不变，只有 `src/reasoning/` 内部实现可替换：

```
answer_query(graph, query, config) -> Answer        # 唯一入口，签名不变
   ├── causal_tracing.py          → 多条因果链（每原因一条）+ 必要因 + 枢纽
   ├── situation_deduction.py     → 完整可能性树（所有分支）+ 最终态势
   ├── counterfactual.py          → 级联消去 + PN/PS/PNS + 连带消失节点
   ├── graph_algorithms.py        → 所有图算法原语（cause_chains/effect_chains/scenario_tree/cascade_removal/necessity/…）
   └── evidence_chain.py          → 证据链工具（未改动）
```

**升级路线：**

1. **PN/PS 从"确定性图估计"升级为"概率估计"**：现在每条边一个标量置信度；未来可在边上放条件概率表（CPT），用信念传播算 PN/PS。
2. **引入时序**：给边加 `time_lag`/时间窗，用动态贝叶斯网或 Hawkes 过程做带时间的态势推演。
3. **引入 LLM 受控推演**：图证据链作为 prompt 上下文，LLM 生成自然语言推演，但结论仍必须被图证据约束（可参考 LLM 因果推理综述）。
4. **可扩展算法开关**：在 `configs/*.yaml` 的 `reasoning.*` 下加 `method` 字段，仿照 `counterfactual.method: ablation` 的既有模式，做 `ablation / probabilistic / llm` 多实现切换。

**相关扩展文献：**

- J. Pearl & D. Mackenzie, *The Book of Why*, Basic Books, 2018 —— 三阶层级最通俗的入口。
- P. Spirtes, C. Glymour, R. Scheines, *Causation, Prediction, and Search*, MIT Press, 2000 —— 因果发现（如果赛题要求从数据直接学图）。
- LLM 因果推理综述（"Causal Inference with Large Language Model: A Survey"，arXiv 2024）——见文末检索链接。
- M. Sundararajan, A. Taly, Q. Yan, "Axiomatic Attribution for Deep Networks," *ICML*, 2017（Integrated Gradients，可解释归因的邻接方法）。
- P. Koh & P. Liang, "Understanding Black-box Predictions via Influence Functions," *ICML*, 2017（影响力函数，可解释归因的邻接方法）。

---

## 5. 参考文献与检索入口

权威书籍/经典论文（可直接按题名检索）：

- Pearl, *Causality* (2000/2009)；Pearl, *Probabilistic Reasoning* (1988)；Pearl & Mackenzie, *The Book of Why* (2018)。
- Pearl, Glymour, Jewell, *Causal Inference in Statistics: A Primer* (2016)。
- Balke & Pearl (UAI 1994)；Tian & Pearl (AMAI 2000)；Pearl (Synthese 1999)；Halpern & Pearl (BJPS 2005)。
- Koller & Friedman, *Probabilistic Graphical Models* (2009)；Murphy, DBN thesis (2002)。
- Endsley (Human Factors 1995)；Steinberg et al., JDL revisions (1999)。
- Wachter et al. (2018)；Mothilal et al. (FAT* 2020)；Karimi et al. (ACM CSUR 2022)。

在线检索起点（近期综述与工程实践）：

- [Causal Inference with Large Language Model: A Survey（LLM 因果推理综述）](https://www.semanticscholar.org/paper/Causal-Inference-with-Large-Language-Model%3A-A-Ma/81b14929edebea495a22ab06b658c284a2ec4710)
- [A Critical Review of Causal Reasoning Benchmarks for Large Language Models](https://aitopics.org/doc/arxivorg:C537E779)
- [Surveying Root Cause Analysis Techniques（多服务应用的根因分析综述）](https://ieeexplore.ieee.org/document/11245222)
- [BARO: Robust Root Cause Analysis for Microservices（贝叶斯在线变点检测的根因定位）](https://dl.acm.org/doi/10.1145/3660805)

> 说明：工程类论文（如 MicroRCA / CausalRCA 的具体卷期页码）请以上方综述或学术搜索引擎核验为准；
> 本框架的算法实现不依赖这些论文的具体编号，只依赖其"因果图 + 概率 + 干预"的方法论内核。
