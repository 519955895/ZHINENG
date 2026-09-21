# 模块3 开发说明：图谱构建 + 推理问答（成员 C）

## 任务（两块）

1. **图谱构建**：把事件 + 因果对组装为有向因果图；
2. **推理问答**：在图 + 证据约束下回答三类问题。

## 入口

```python
# 建图
from src.graph import build_graph, to_networkx
build_graph(events, relations) -> CausalGraph
to_networkx(graph) -> nx.DiGraph

# 推理
from src.reasoning import answer_query
answer_query(graph, query, config) -> Answer
```

## 建议文件划分

| 文件 | 职责 |
|------|------|
| `graph/graph_builder.py` | 建图、节点合并、冲突边处理 |
| `graph/graph_store.py` | 序列化 / 导出（可加 GEXF 可视化） |
| `reasoning/causal_tracing.py` | 因果追溯 |
| `reasoning/situation_deduction.py` | 态势推演 |
| `reasoning/counterfactual.py` | 反事实推理 |
| `reasoning/evidence_chain.py` | 证据链生成工具 |

## 一、图谱构建

- **节点合并**：同一事件被多次抽取（不同文档或重复 mention），按 `mention` 相似度合并，
  保留置信度最高的一条，其余事件 id 建立别名映射。
- **冲突边处理**：A→B 与 B→A 同时出现时，按 config 的 `conflict_strategy` 处理
  （`keep_both` / `max_conf` 取高置信 / `min_conf` 取低置信）。
- **元信息**：统计节点数、边数、密度、最大入/出度，写入 `metadata`。

> 三类推理的**论文推荐 + 方法升级版**见 [`docs/reasoning_methods.md`](reasoning_methods.md)；
> 本文件保留基线做法的说明，升级实现见 `src/reasoning/graph_algorithms.py` 及各推理文件。

## 二、推理问答

### 1. 因果追溯（causal_tracing）
- 定位问题锚定的事件节点（`seed_event_ids` 或从 question 中匹配）；
- **回溯**：用 `nx.ancestors` / 前驱路径，找所有上游原因，形成原因链；
- **前瞻**：用 `nx.descendants` / 后继路径，找下游影响；
- 证据链 = 路径上经过的边 id，用 `collect_evidence` 回填原文。

### 2. 态势推演（situation_deduction）
- 从种子事件出发，沿因果边**前向多跳**传播；
- 用 `nx.DiGraph` 的 BFS/DFS 展开，结合边置信度估计触发概率；
- 输出"最可能的后续事件链 + 依据"。

### 3. 反事实推理（counterfactual）
- **删边模拟（推荐先做）**：假设"原因 A"未发生，临时删掉 A 的所有出边，
  重算目标 B 的可达原因集合；若 B 仍可达，说明 B 还有其它原因路径；否则 B 依赖 A。
- **生成式（进阶）**：用证据链组织上下文，交给 LLM 做受控推演，结论仍需受图证据约束。
- 输出要对比"有 A"与"无 A"两种情况的差异。

## 输出质量自查清单

- [ ] 图结构正确：节点=事件，边=因果，方向正确；
- [ ] 三类问题都返回非空 `answer_text` 且带 `evidence_chain`；
- [ ] 追溯答案的因果链在图上是连通的；
- [ ] 反事实答案明确说明"删掉 X 后，结果是否仍会发生、依据是什么"。

## 与上游协作

- 你需要 `to_networkx` 做图算法；若成员 B 的关系质量差（方向错、缺证据），图会噪声大，
  请把 bad case 反馈给 B。
- 可视化建议：导出 GEXF 用 Gephi 看大图结构，辅助调参和答辩展示。
