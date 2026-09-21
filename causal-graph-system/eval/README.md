# 真实新闻因果图谱推理 —— 测试集与评测结果

本目录存放 **10 条真实新闻** 的因果图谱测试集，以及用框架三类推理方法（因果追溯 / 态势推演 / 反事实）跑出的结果，方便逐题对照查看。

## 目录结构

```
eval/
├── run_eval.py             # 一键评测脚本（重新生成 testset 与 results）
├── README.md               # 本说明
├── testset/
│   ├── news_01.json        # 河南开封/郑州暴雨红色预警（自然灾害·城市内涝）
│   ├── news_02.json        # 福建莆田持续强降雨·三停一休（自然灾害）
│   ├── news_03.json        # 车规芯片缺货涨价·车企停产（供应链·汽车芯片）
│   ├── news_04.json        # 四川高温限电·水泥停窑（能源·高温限电）
│   ├── news_05.json        # 美国西部山火·毒烟撤离（自然灾害·山火）
│   ├── news_06.json        # 加拿大山火烟雾·健康威胁（自然灾害·山火）
│   ├── news_07.json        # 红海危机绕行·运费激增（航运·供应链）
│   ├── news_08.json        # 欧洲港口罢工·货物滞留（航运·港口）
│   ├── news_09.json        # 厄尔尼诺·农作物减产·食品涨价（农业·粮食）
│   └── news_10.json        # 粮食供应风险·食品价格·通胀（经济·通胀）
└── results/
    ├── results_all.json    # 机器可读：30 个问答的完整答案 + 证据链 + 元数据
    └── report.md           # 人类可读：逐条新闻 + 逐题对照（含图谱边、答案文本）
```

## 每个 news_XX.json 的内容

```jsonc
{
  "news_id": "news_01",
  "domain": "自然灾害·城市内涝",
  "date": "2024-07",
  "title": "...",
  "source_url": "https://...",       // 报道来源
  "events":  [ {event_id, trigger, mention, event_type, confidence, ...} ],
  "relations":[ {relation_id, cause_event_id, effect_event_id, relation_type, evidence, confidence} ],
  "queries": [ {query_id, question, question_type} ]   // 每篇 3 问
}
```

- `events` / `relations` / `queries` 字段与 `src/common/schemas.py` 契约一致；
- 因果图由报道标题/要点重建，`evidence` 为报道要点，`confidence` 为演示赋值；
- 每篇 3 个问题固定覆盖三类推理：`causal_tracing` / `situation_deduction` / `counterfactual`。

## 复现方式

```bash
py eval/run_eval.py
```

脚本会：加载 10 条新闻 → `build_graph` 建图 → `answer_query` 逐题推理 → 写出 `testset/` 与 `results/`。

## 结果速览（10 条全部跑通）

| 新闻 | 节点/边 | 反事实 Q3 结论 | PN | PS |
|------|--------:|---------------|----|----|
| news_01 河南暴雨 | 6/7 | 拔掉公交停运，出行受阻仍经"内涝"发生 | 0.23 | 0.84 |
| news_02 莆田强降雨 | 5/4 | 拔掉内涝，抢险随级联消失 | 1.00 | 0.77 |
| news_03 芯片缺货 | 5/5 | 拔掉车企停产，车价仍经"芯片涨价"上涨 | 0.34 | 0.72 |
| news_04 四川限电 | 7/6 | 拔掉限电，水泥产量下降随级联消失 | 1.00 | 0.66 |
| news_05 美国山火 | 5/5 | 拔掉毒烟，撤离与健康威胁随级联消失 | 1.00 | 0.82 |
| news_06 加拿大山火 | 5/4 | 拔掉空气质量恶化，户外取消随级联消失 | 1.00 | 0.78 |
| news_07 红海危机 | 5/4 | 拔掉绕行，运费与成本随级联消失 | 1.00 | 0.61 |
| news_08 港口罢工 | 5/4 | 拔掉港口停摆，应急响应随级联消失 | 1.00 | 0.61 |
| news_09 厄尔尼诺 | 5/4 | 拔掉减产，食品涨价随级联消失 | 1.00 | 0.70 |
| news_10 食品通胀 | 4/3 | 拔掉食品涨价，购买力下降随级联消失 | 1.00 | 0.68 |

> 说明：news_01 与 news_03 是"多因汇入"（钻石结构），所以拔掉单一原因后目标仍有替代路径、PN<1；
> 其余多为单链结构，根因/中间环节一旦拔掉即级联崩塌、PN=1。
> 完整 30 题答案见 `results/report.md`。
