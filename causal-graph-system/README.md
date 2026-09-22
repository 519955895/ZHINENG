# 新闻事件因果图谱与推理系统

面向「大数据智能算法设计运用大赛」赛题 **《面向信息挖掘与辅助决策的业务需求》** 的整体工程框架。

本系统从多篇新闻文档出发，自动完成：**事件抽取 → 因果关系识别 → 因果图谱构建 → 证据约束推理问答**，
支持赛题的三档渐进式难度（基础档 / 推理档 / 挑战档）。

---

## 一、赛题与系统定位

| 档位 | 给定输入 | 系统需要完成的工作 |
|------|----------|-------------------|
| **基础档** | 已提供因果图 | 仅做**图谱理解 + 推理问答**（因果追溯 / 态势推演 / 反事实） |
| **推理档** | 仅提供事件列表 | 事件 → **因果关系识别** → 建图 → 推理问答 |
| **挑战档** | 仅原始文档 | 文档 → **事件抽取** → 关系识别 → 建图 → 推理问答 |

三个档位共享同一套数据结构与推理问答模块，只是**从不同的流水线起点切入**，保证算法可复用、可渐进升级。

---

## 二、三人分工与模块映射

| 成员 | 负责模块 | 源码目录 | 输入 | 输出 |
|------|---------|---------|------|------|
| **A · 内容抽取** | 模块 1：事件抽取 | `src/extraction/` | 原始文档 | 事件列表（`Event`） |
| **B · 关系建立** | 模块 2：因果识别 | `src/relation/` | 事件列表 | 因果对（`CausalRelation`） |
| **C · 图谱构建** | 模块 3：建图 + 推理问答 | `src/graph/`、`src/reasoning/` | 因果对 → 图谱 → 问题 | 答案（`Answer`） |

三人之间**只通过统一的 JSON 数据结构（契约）衔接**，互不依赖对方的内部实现。
契约定义在 [`src/common/schemas.py`](src/common/schemas.py)，完整约定见 [`docs/interface.md`](docs/interface.md)。

---

## 三、目录结构

```
causal-graph-system/
├── README.md                     # 本文件：总体说明
├── requirements.txt              # 依赖清单
├── configs/                      # 三档运行配置
│   ├── basic.yaml                # 基础档：直接读图 + 推理
│   ├── reasoning.yaml            # 推理档：事件列表起步
│   └── challenge.yaml            # 挑战档：原始文档起步
├── data/                         # 数据目录（版本化管理中间产物）
│   ├── raw/                      #   原始新闻文档
│   ├── events/                   #   事件列表（模块1产物）
│   ├── relations/                #   因果对（模块2产物）
│   ├── graphs/                   #   因果图谱（模块3产物）
│   └── output/                   #   最终答案
├── src/
│   ├── common/                   # 公共层：数据结构、IO、配置、日志
│   ├── extraction/               # 模块1：新闻内容抽取（成员 A）
│   ├── relation/                 # 模块2：因果关系建立（成员 B）
│   ├── graph/                    # 模块3：图谱构建（成员 C）
│   ├── reasoning/                # 模块3续：推理问答（成员 C）
│   └── pipeline/                 # 编排层：三档入口，串起各模块
├── docs/                         # 说明文档
│   ├── architecture.md           #   总体架构与数据流
│   ├── interface.md              #   三人协作接口契约（必读）
│   ├── module1_extraction.md     #   模块1开发说明
│   ├── module2_relation.md       #   模块2开发说明
│   └── module3_graph.md          #   模块3开发说明
├── scripts/
│   ├── run_pipeline.py           # 一键运行入口
│   └── eval.py                   # 评测脚本
└── tests/                        # 单元测试
```

---

## 四、快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 挑战档（全流程，从原始文档开始）
python scripts/run_pipeline.py --config configs/challenge.yaml

# 3. 推理档（从事件列表开始）
python scripts/run_pipeline.py --config configs/reasoning.yaml

# 4. 基础档（从因果图开始）
python scripts/run_pipeline.py --config configs/basic.yaml

# 5. 跑测试
python -m pytest tests/
```

---

## 五、统一数据契约（核心，先看这里）

三个模块之间的"交接物"只有三种，全部定义在 `src/common/schemas.py`：

```jsonc
// ① 事件 Event（模块1产出 → 模块2消费）
{
  "event_id": "E001",
  "doc_id": "D001",
  "event_type": "灾害/事故",
  "trigger": "发生",
  "arguments": [{"role": "subject", "value": "暴雨"}],
  "time": "2024-07-01", "location": "郑州",
  "mention": "郑州发生暴雨", "char_offset": [12, 19],
  "confidence": 0.93
}

// ② 因果对 CausalRelation（模块2产出 → 模块3消费）
{
  "relation_id": "R001",
  "cause_event_id": "E001",
  "effect_event_id": "E002",
  "relation_type": "causal",          // causal/enables/prevents/conditional
  "evidence": ["因为暴雨，道路积水严重"],
  "confidence": 0.88
}

// ③ 因果图谱 CausalGraph（模块3构建）+ 答案 Answer（推理产出）
```

> 详细字段含义、类型、必填项见 [`docs/interface.md`](docs/interface.md)。

---

## 六、数据流总览

```
        ┌──────────────┐
        │  原始新闻文档  │  (challenge 起点)
        └──────┬───────┘
               │  模块1 事件抽取
        ┌──────▼───────┐
        │   事件列表     │  (reasoning 起点)
        └──────┬───────┘
               │  模块2 因果识别
        ┌──────▼───────┐
        │    因果对      │
        └──────┬───────┘
               │  模块3 图谱构建
        ┌──────▼───────┐
        │   因果图谱     │  (basic 起点)
        └──────┬───────┘
               │  推理问答（因果追溯/态势推演/反事实）
        ┌──────▼───────┐
        │   答案 Answer  │
        └──────────────┘
```

---

## 七、协作约定

1. **只认契约不认实现**：任何人修改 `schemas.py` 必须同步更新 `docs/interface.md` 并在群内告知。
2. **中间产物落盘为 JSONL/JSON**：方便各模块独立调试、断点续跑、人工抽查。
3. **每个模块对外只暴露一个入口函数**（如 `extract_events(docs) -> List[Event]`），签名写在各自目录 `__init__.py`。
4. **用 `data/` 版本化管理产物**：抽取结果错了，关系、建图直接复用即可，不用重跑上游。
5. **证据链是硬约束**：所有答案必须携带 `evidence_chain`，追溯到原文片段。

---

## 八、里程碑建议（三人并行开发）

- **第 1 周**：冻结 `schemas.py` 契约 + 造好假数据样例 + 各模块跑通空实现（`NotImplementedError` 替换为真实逻辑）。
- **第 2 周**：模块 1 完成事件抽取；模块 2 先上规则/提示词基线；模块 3 完成建图与最简路径检索。
- **第 3 周**：模块 2 升级判别/生成式模型；模块 3 完成三类推理问答（先做因果追溯，再做反事实）。
- **第 4 周**：三档联调、补证据约束、写评测、调 prompt/阈值，冲刺。
