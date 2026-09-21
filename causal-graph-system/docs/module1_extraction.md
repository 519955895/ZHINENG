# 模块1 开发说明：新闻内容抽取（成员 A）

## 任务

从多篇原始新闻文档中抽取**原子事件**，输出标准 `Event` 列表。

## 入口

`src/extraction/event_extractor.py` 中的：

```python
def extract_events(documents: List[Document]) -> List[Event]:
```

## 建议文件划分

| 文件 | 职责 |
|------|------|
| `event_extractor.py` | 主入口，串起下列子模块 |
| `ner.py` | 命名实体识别（人物/机构/地点/时间） |
| `event_type_cls.py` | 事件类型分类 |
| `argument_role.py` | 论元角色识别与填充 |
| `coreference.py` | （可选）指代消解，解决"它/该公司"回指 |

## 技术路线（渐进式）

1. **规则基线（先跑通）**
   - 构建触发词词典：`发生/宣布/上涨/下降/出台/造成/爆发/签署/发布…`
   - 正则 + jieba 分词定位触发词，抓取周边论元；
   - 用简单规则映射事件类型。

2. **NER 升级**
   - 用 `spacy` / `hanlp` / `LTP` 做实体识别；
   - 时间、地点用规则归一化（"昨天" → 具体日期需结合 publish_time）。

3. **序列标注 / 生成式升级**
   - 序列标注：BIO 标注触发词 + 论元（需自建标注数据）；
   - 生成式：UIE、或大模型少样本 prompt 直接抽取结构化事件 JSON。

## 输出质量自查清单

- [ ] 每个事件 `mention` 能在原文中找到，`char_offset` 正确；
- [ ] `event_type` 属于团队统一类型表；
- [ ] 论元角色与值对应正确（subject 是施事不是受事）；
- [ ] 时间/地点已归一化，可供下游做时序约束；
- [ ] `confidence` 有区分度（不是全部 1.0）。

## 与下游协作

- 产出写到 `data/events/*.jsonl`（编排器自动做，你也可以手动调 `io_utils.save_events` 自查）；
- 若你发现某类事件很难抽，**尽早把案例丢给成员 B**，让他的关系模块对这类事件有预期。
