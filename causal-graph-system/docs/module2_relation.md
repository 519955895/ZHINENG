# 模块2 开发说明：因果关系建立（成员 B）

## 任务

在给定事件列表上，识别事件两两之间的**因果关系**，输出 `CausalRelation` 列表。

## 入口

`src/relation/causal_relation.py` 中的：

```python
def extract_relations(events: List[Event]) -> List[CausalRelation]:
```

## 建议文件划分

| 文件 | 职责 |
|------|------|
| `causal_relation.py` | 主入口，串起下列子模块 |
| `cue_pattern.py` | 因果提示词 + 规则模式匹配 |
| `classifier.py` | 判别式/生成式因果判定 |
| `evidence_alignment.py` | 把判定的因果对回填原文证据 |

## 技术路线（渐进式）

1. **规则基线（先跑通）**
   - 因果提示词：`导致/引起/因为/致使/造成/引发/由于/后果/使得/从而…`
   - 候选对生成：同句 / 同段 / 时间先后（因先于果）的共现事件对；
   - 依据提示词方向确定 cause/effect，关系类型暂全标 `causal`。

2. **判别式升级**
   - 构造 (event_a, event_b, context) 样本，用 BERT 二分类判断是否因果；
   - 正例来自提示词规则命中，负例来自随机配对，人工抽查校正。

3. **生成式升级**
   - 大模型少样本 prompt，直接输出 `(cause, effect, type, evidence)`；
   - 显式要求模型**引用原文片段**作为 evidence，与证据约束对齐。

4. **进阶**
   - 隐式因果：无提示词但语义上是因果（"下雨了，地面湿了"）；
   - 跨句/跨文档因果：结合事件共指与时序；
   - 关系类型细分：causal / enables / prevents / conditional。

## 输出质量自查清单

- [ ] `cause_event_id` / `effect_event_id` 都存在于输入 events 中；
- [ ] 方向正确（别把因果写反）；
- [ ] 每条关系有 `evidence`（原文片段），且证据能支撑该因果；
- [ ] 关系类型不为空，且属于四类之一；
- [ ] `confidence` 有区分度。

## 与上下游协作

- **上游（成员 A）**：event 的 `mention`、`time`、`location` 是你做共现/时序的关键字段；若缺失，请反馈 A 补充。
- **下游（成员 C）**：你产出的 evidence 会直接变成最终答案的证据链，务必保证证据真实、指向明确。
