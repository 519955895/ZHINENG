# 数据目录说明

本目录存放输入与各阶段中间产物，**按目录分类、版本化管理**：

```
data/
├── raw/         原始新闻文档 + 问题列表（输入）
├── events/      事件列表（模块1产物，*.jsonl）
├── relations/   因果对（模块2产物，*.jsonl）
├── graphs/      因果图谱（模块3产物，*.json）
└── output/      最终答案（推理产物，answers.json）
```

约定：
- 中间产物可手动查看/纠错后回填，供下游断点续跑；
- 目录里已放 `raw/news_sample.json` 与 `raw/queries_sample.json` 作为格式示例；
- 正式数据请替换/新增到对应目录，并在配置文件的 `paths` 里指定路径。
