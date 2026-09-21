# 因果图谱推理 · 可视化前端

一个"蓝黄央视新闻配色"的可视化小前端，用于对因果图谱做 **导入 → 分析 → 因果追溯 / 态势推演 / 反事实推理 → 结果展示**。

## 运行

```bash
py web/app.py
```

浏览器打开 **http://127.0.0.1:8000** 即可。

- 后端是 **零依赖** 的 Python 标准库 `http.server`（本沙箱无法安装 FastAPI，故以标准库实现相同接口；`src/` 推理逻辑直接复用）。
- 图谱渲染用 **ECharts**（CDN 引入：bootcdn 主源 + jsdelivr 备源）。

## 功能

| 区域 | 说明 |
|------|------|
| 顶栏 | 选择预置数据集（10 条新闻 + 示例图）、**导入图谱**（上传 JSON）、分析/重置 |
| 图谱 | ECharts 力导向图；节点按事件类型着色、大小按度数；边带 `relation_type`/置信度，悬停看证据 |
| 图谱分析 | 节点数 / 边数 / 密度、根事件、末端事件、关系类型分布、PageRank 关键枢纽 |
| 推理操作 | 三个标签页：因果追溯 / 态势推演 / 反事实推理；支持预设问题、点击节点生成问题、自由输入 |
| 结果 | 答案文本 + 置信度 + 证据链（图中高亮为金黄）+ 元数据（PN/PS/PNS 等） |

## 导入图谱的 JSON 格式

两种都支持（与 `src/common/schemas.py` 契约一致）：

1. **CausalGraph 格式**：`{"graph_id": "...", "nodes": [{...Event}], "edges": [{...CausalRelation}]}`
2. **事件+关系格式**：`{"events": [{...Event}], "relations": [{...CausalRelation}]}`（自动 `build_graph`）

示例文件：`data/graphs/graph_dev.json`、`eval/testset/news_01.json`。

## 接口（供扩展）

```
GET  /api/datasets     数据集列表
POST /api/load         {dataset_id}                     → 图谱+分析+预设问题
POST /api/upload       {graph: {...}}                   → 图谱+分析
POST /api/query        {question, question_type}        → Answer（answer_text/evidence_chain/confidence/metadata）
```

## 说明

- **ECharts 离线化**：若需完全离线，把 `echarts.min.js` 下载到 `web/static/vendor/echarts.min.js`，
  并在 `index.html` 里把两个 CDN `<script>` 换成 `/static/vendor/echarts.min.js`（本沙箱 HTTPS 被 TLS 凭证限制，无法替你下载）。
- **换 FastAPI**：若在你本地环境可 `pip install fastapi uvicorn`，接口一一对应，把 `web/app.py` 的
  `http.server` 层替换为 FastAPI 路由即可，`_load_news/to_echarts/analyze/api_query` 等函数无需改动。
