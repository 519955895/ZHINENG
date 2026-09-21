# 三人分开开发后如何合并（集成手册）

## 一、核心结论：因为"契约 + 接口骨架"已就位，合并几乎无冲突

系统在设计时就把三个模块**彻底解耦**了：

- 模块之间**只传数据、不传代码**，交接物是 `Event` / `CausalRelation` / `CausalGraph` 这些 JSON 结构；
- 编排器 `src/pipeline/orchestrator.py` 只调用 4 个**固定签名**的入口函数；
- 每个模块目录里已放好带 `NotImplementedError` 的骨架，等你把函数体填上即可。

因此合并的本质是：**各人只改自己的目录，最后把三份改动合到一起**。

## 二、文件所有权（谁只能碰哪些文件）

| 文件/目录 | 所有者 | 说明 |
|-----------|--------|------|
| `src/extraction/` | 成员 A | 模块1，只改这里 |
| `src/relation/` | 成员 B | 模块2，只改这里 |
| `src/graph/`、`src/reasoning/` | 成员 C | 模块3，只改这里 |
| `src/common/schemas.py` | **全队共管** | 改前必须群内协商 |
| `src/common/`（其余）| 全队共管 | 一般不用改 |
| `src/pipeline/` | 全队共管 | 一般不用改 |
| `configs/` | 全队共管 | 调参可改，别改路径字段 |
| `data/`、`scripts/` | 各自/共享 | 调试产物 |

**纪律**：除非全队同意，否则不碰别人目录、不碰公共层。这样即使不做任何版本管理，合并也只是"把三个目录的改动拼在一起"。

## 三、合并方式（二选一）

### 方式一：Git 分支（推荐）

```bash
# 1. 建仓，main 放公共骨架（就是当前这份代码）
git init
git add -A && git commit -m "init: 公共骨架 + 契约 + 编排层"

# 2. 三人各自拉分支（以 A 为例）
git checkout -b feature/extraction   # B: feature/relation, C: feature/graph
# ... A 只改 src/extraction/ 并提交 ...

# 3. 各自把分支推到远端 / 或本地合并回 main
git checkout main
git merge feature/extraction
git merge feature/relation
git merge feature/graph
# 因为改动文件互不重叠，基本零冲突
```

> 若三人共用一台机器/一个目录而没有远端，也可用 `git worktree` 或干脆用下面的"拷贝法"。

### 方式二：文件拷贝（不熟悉 git）

1. 把这份骨架复制三份，三人各自开发**自己的目录**；
2. 交付时，每人只提交自己目录：A 交 `src/extraction/`、B 交 `src/relation/`、C 交 `src/graph/` + `src/reasoning/`；
3. 一个人把三份目录**拷回**骨架对应位置（公共层用骨架原件即可）；
4. 运行 `py scripts/smoke_test.py` 验证。

## 四、并行开发的三个检查点

关键在于**每个人都能独立开发、独立调试，不必等别人**。为此我准备了"示例中间产物"，让下游不用等上游：

| 检查点 | 谁 | 独立调试脚本 | 输入（示例） |
|--------|----|-------------|-------------|
| 事件抽取跑通 | A | `py scripts/dev_extraction.py` | `data/raw/news_sample.json` |
| 因果识别跑通 | B | `py scripts/dev_relation.py` | `data/events/events_sample.jsonl`（A 未完成也能用） |
| 建图+推理跑通 | C | `py scripts/dev_graph.py` | `data/events/events_sample.jsonl` + `data/relations/relations_sample.jsonl` |

> 示例中间产物（`*_sample.jsonl`）与示例文档内容**一一对应**，B、C 用它开发，等 A、B 实现后把输入路径换成 `*_dev.jsonl` 即可无缝衔接。

## 五、联调流程（按阶段推进）

1. **阶段1（各自开发）**：三人用上面的独立脚本各自跑通，互不阻塞。
2. **阶段2（文件交接）**：A 把真实 `events_dev.jsonl` 给 B；B 把真实 `relations_dev.jsonl` 给 C。
   这一步即使代码没合并，也能靠**文件交接**先验证数据对不对。
3. **阶段3（代码合并）**：把三人目录合并回一份，跑 `py scripts/smoke_test.py`；
   它按挑战档顺序串起三模块 + 三类推理，逐段报 PASS/FAIL，是全队的"验收门槛"。
4. **阶段4（端到端）**：`py scripts/run_pipeline.py --config configs/challenge.yaml` 跑正式数据。

## 六、契约变更流程（改 schemas.py 时）

1. 在 `src/common/schemas.py` 改字段；
2. 同步更新 `docs/interface.md` 对应字段表；
3. 群内告知"契约变更 + 影响范围"；
4. 其他成员同步更新自己模块的 `to_dict`/`from_dict` 消费逻辑。

> 常见易变点：新增事件类型、新增 relation_type、给 Event 加字段。加字段时给默认值，避免下游崩。

## 七、合并后常见问题排查

| 现象 | 原因 | 处理 |
|------|------|------|
| `from_dict` 报 `TypeError` 缺参数 | 上游加了字段但下游 schema 没同步 | 对齐 `schemas.py`，加默认值 |
| 答案 `evidence_chain` 为空 | 成员 C 没调用 `collect_evidence` | 见 `reasoning/evidence_chain.py` |
| 图里出现孤立点 | 成员 B 漏了某些事件的因果对 | 检查 `relations_sample.jsonl` 覆盖是否完整 |
| `run_pipeline` 找不到输入文件 | config 的 `paths` 与实际文件名不一致 | 对齐文件名与 `configs/*.yaml` |
