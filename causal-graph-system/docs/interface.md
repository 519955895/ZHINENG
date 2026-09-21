# 接口契约（三人协作必读）

> 本文件是三人之间的"合同"。所有数据结构的权威定义在 `src/common/schemas.py`，
> 本文档是它的**人类可读说明**。改 schema 必须同步改这里。

## 1. 总原则

- 模块间**只传数据、不传代码**：A 产出 `Event` 列表，B 消费它；B 产出 `CausalRelation` 列表，C 消费它。
- 所有产物落盘为 **JSON（单对象）或 JSONL（列表，每行一个对象）**。
- `*_id` 全局唯一，前缀约定：`D`=文档、`E`=事件、`R`=关系、`G`=图、`Q`=问题。
- 所有 `confidence` ∈ [0,1]。

## 2. Document（原始文档）

```json
{
  "doc_id": "D001",
  "title": "暴雨导致城市内涝",
  "text": "7月1日，郑州市遭遇强暴雨……",
  "source": "示例媒体",
  "publish_time": "2024-07-01",
  "metadata": {}
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| doc_id | str | ✅ | 文档唯一 id |
| title | str | ✅ | 标题 |
| text | str | ✅ | 正文全文 |
| source | str | | 来源媒体 |
| publish_time | str | | ISO 时间 |
| metadata | dict | | 其它字段 |

## 3. Event（事件，模块1→模块2）

```json
{
  "event_id": "E001",
  "doc_id": "D001",
  "event_type": "灾害/事故",
  "trigger": "发生",
  "mention": "郑州市遭遇强暴雨",
  "arguments": [
    {"role": "location", "value": "郑州市"},
    {"role": "subject", "value": "强暴雨"}
  ],
  "time": "2024-07-01",
  "location": "郑州市",
  "char_offset": [0, 9],
  "confidence": 0.93
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| event_id | str | ✅ | 事件唯一 id |
| doc_id | str | ✅ | 所属文档 |
| event_type | str | ✅ | 事件类型（见下方类型表） |
| trigger | str | ✅ | 触发词 |
| mention | str | ✅ | **原文片段**，证据追溯关键 |
| arguments | list[Argument] | | 论元（role/value） |
| time | str | | 归一化时间 |
| location | str | | 归一化地点 |
| char_offset | [int,int] | | 原文字符偏移 |
| confidence | float | ✅ | 置信度 |

**Argument.role 建议值**：`subject`（施事/主体）、`object`（受事/客体）、
`time`、`location`、`instrument`（工具）、`manner`（方式）、`result`（结果）。

**event_type 建议值**（可扩展，但要团队统一）：

| 类型 | 示例 |
|------|------|
| 灾害/事故 | 暴雨、地震、火灾、车祸 |
| 政策/发布 | 颁布、出台、宣布 |
| 经济/涨跌 | 上涨、下跌、裁员 |
| 社会/舆情 | 抗议、集会、传播 |

## 4. CausalRelation（因果对，模块2→模块3）

```json
{
  "relation_id": "R001",
  "cause_event_id": "E001",
  "effect_event_id": "E002",
  "relation_type": "causal",
  "evidence": ["暴雨导致多处道路积水严重"],
  "confidence": 0.88,
  "time_lag": "immediate"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| relation_id | str | ✅ | 关系唯一 id |
| cause_event_id | str | ✅ | 原因事件 id |
| effect_event_id | str | ✅ | 结果事件 id |
| relation_type | str | ✅ | 见下表 |
| evidence | list[str] | ✅ | **原文证据片段** |
| confidence | float | ✅ | 置信度 |
| time_lag | str | | immediate/days/years |

**relation_type 约定**（定义在 schemas.py 常量）：

| 值 | 含义 | 示例 |
|----|------|------|
| `causal` | 直接因果 | 暴雨 → 道路积水 |
| `enables` | 使能 | 积水 → 抛锚（提供条件） |
| `prevents` | 抑制 | 排水 → 阻止积水 |
| `conditional` | 条件 | 若持续降雨 → 则水位上涨 |

## 5. CausalGraph（图谱，模块3构建）

```json
{
  "graph_id": "G001",
  "nodes": [ { ...Event... } ],
  "edges": [ { ...CausalRelation... } ],
  "metadata": { "node_count": 5, "edge_count": 4, "density": 0.2 }
}
```

节点即事件，边即因果对，方向 `cause → effect`。

## 6. Query 与 Answer（推理问答）

```jsonc
// Query
{
  "query_id": "Q001",
  "question": "是什么导致了道路积水严重？",
  "question_type": "causal_tracing",      // causal_tracing | situation_deduction | counterfactual
  "seed_event_ids": ["E002"]
}

// Answer（必须带证据链）
{
  "query_id": "Q001",
  "question_type": "causal_tracing",
  "answer_text": "暴雨（E001）导致道路积水（E002）。",
  "evidence_chain": ["R001", "E001", "E002"],   // 命中的边/节点 id，有序
  "confidence": 0.9,
  "metadata": {}
}
```

**三类问题**：

| question_type | 问法示例 | 目标 |
|---------------|---------|------|
| causal_tracing | 什么导致/引发了 X？ | 上游原因链（回溯）或下游影响链（前瞻） |
| situation_deduction | X 可能引发什么？ | 沿因果边前向多跳推演态势 |
| counterfactual | 若 A 没发生，B 会怎样？ | 删边模拟 / 生成式反事实，对比差异 |

## 7. 各模块对外入口函数（唯一对接点）

| 模块 | 入口 | 签名 |
|------|------|------|
| 模块1 | `extraction.extract_events` | `(List[Document]) -> List[Event]` |
| 模块2 | `relation.extract_relations` | `(List[Event]) -> List[CausalRelation]` |
| 模块3 | `graph.build_graph` | `(List[Event], List[CausalRelation]) -> CausalGraph` |
| 推理 | `reasoning.answer_query` | `(CausalGraph, Query, config?) -> Answer` |

> 编排器只调用这四个函数。**任何人不得修改函数签名**；要加参数只能加默认参数或放进 config。

## 8. 变更流程

1. 修改 `src/common/schemas.py`；
2. 同步更新本 `interface.md` 对应字段表；
3. 在群内告知"契约变更 + 影响范围"；
4. 其它成员按需更新 `from_dict`/`to_dict` 的消费逻辑。
