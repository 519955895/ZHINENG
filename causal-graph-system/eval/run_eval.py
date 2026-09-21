"""真实新闻因果图谱测试集 + 一键评测。

用法：py eval/run_eval.py
产出：
  eval/testset/news_XX.json       —— 10 条新闻（事件 + 因果对 + 问题，含来源）
  eval/results/results_all.json   —— 机器可读的全部答案
  eval/results/report.md          —— 人类可读的逐题对比报告

说明：因果图由各报道的标题/要点重建，边上的 evidence 为报道要点，
      confidence 为对"该因果链接成立程度"的人工赋值（演示用）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.schemas import (  # noqa: E402
    CausalRelation, Event, QT_CAUSAL_TRACING, QT_COUNTERFACTUAL, QT_SITUATION_DEDUCTION, Query,
)
from src.graph import build_graph  # noqa: E402
from src.reasoning import answer_query  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
TESTSET_DIR = os.path.join(BASE, "testset")
RESULTS_DIR = os.path.join(BASE, "results")


def ev(eid, trigger, mention, etype="事件", conf=0.9):
    return {"event_id": eid, "doc_id": "D0", "event_type": etype, "trigger": trigger,
            "mention": mention, "arguments": [], "time": "", "location": "",
            "char_offset": None, "confidence": conf}


def rel(rid, c, e, evidence, rtype="causal", conf=0.9):
    return {"relation_id": rid, "cause_event_id": c, "effect_event_id": e,
            "relation_type": rtype, "evidence": [evidence], "confidence": conf, "time_lag": ""}


def q(qid, question, qtype):
    return {"query_id": qid, "question": question, "question_type": qtype, "seed_event_ids": []}


NEWS = [
    {
        "news_id": "news_01", "domain": "自然灾害·城市内涝", "date": "2024-07",
        "title": "河南开封发布暴雨红色预警，应急响应升级，郑州/开封部分公交停运、停课停业",
        "source_url": "https://export.shobserver.com/baijiahao/html/770081.html",
        "events": [
            ev("E001", "暴雨", "开封发布暴雨红色预警", "灾害/事故", 0.95),
            ev("E002", "应急响应", "防汛应急响应提升为三级", "政策/发布", 0.92),
            ev("E003", "内涝", "郑州启动蓝色内涝预警（道路积水）", "灾害/事故", 0.90),
            ev("E004", "公交停运", "郑州和开封部分公交停运", "社会/舆情", 0.88),
            ev("E005", "停课停业", "学校停课、商户停业", "政策/发布", 0.90),
            ev("E006", "出行受阻", "市民出行受阻", "社会/舆情", 0.85),
        ],
        "relations": [
            rel("R001", "E001", "E002", "暴雨红色预警，应急响应提升为三级", "causal", 0.90),
            rel("R002", "E001", "E003", "强降雨导致道路内涝", "causal", 0.90),
            rel("R003", "E001", "E005", "暴雨红色预警，学校停课、商户停业", "causal", 0.88),
            rel("R004", "E002", "E004", "应急响应，部分公交停运", "causal", 0.80),
            rel("R005", "E003", "E004", "内涝积水，部分公交停运", "enables", 0.82),
            rel("R006", "E003", "E006", "内涝积水，市民出行受阻", "causal", 0.86),
            rel("R007", "E004", "E006", "公交停运，市民出行受阻", "causal", 0.84),
        ],
        "queries": [
            q("Q1", "是什么导致了市民出行受阻？", QT_CAUSAL_TRACING),
            q("Q2", "暴雨红色预警可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如公交停运没有发生，市民出行受阻还会发生吗？", QT_COUNTERFACTUAL),
        ],
    },
    {
        "news_id": "news_02", "domain": "自然灾害·城市内涝", "date": "2024-09",
        "title": "福建莆田持续强降雨：多人失联，全市停工停产停课休市并全力抢险",
        "source_url": "https://m.gmw.cn/2026-09/04/content_1304559247.htm",
        "events": [
            ev("E001", "强降雨", "福建莆田遭遇持续强降雨", "灾害/事故", 0.95),
            ev("E002", "内涝", "城市内涝积水", "灾害/事故", 0.90),
            ev("E003", "失联", "因强降雨多人失联", "灾害/事故", 0.88),
            ev("E004", "三停一休", "全市启动三停一休（停工停产停课休市）", "政策/发布", 0.90),
            ev("E005", "抢险", "全力抢险救援", "社会/舆情", 0.92),
        ],
        "relations": [
            rel("R001", "E001", "E002", "强降雨导致内涝积水", "causal", 0.90),
            rel("R002", "E002", "E003", "内涝积水导致多人失联", "causal", 0.85),
            rel("R003", "E003", "E005", "多人失联，全力抢险救援", "causal", 0.90),
            rel("R004", "E001", "E004", "强降雨，启动三停一休", "causal", 0.88),
        ],
        "queries": [
            q("Q1", "是什么导致了多人失联？", QT_CAUSAL_TRACING),
            q("Q2", "持续强降雨可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如内涝积水没有发生，全力抢险还会开展吗？", QT_COUNTERFACTUAL),
        ],
    },
    {
        "news_id": "news_03", "domain": "供应链·汽车芯片", "date": "2024",
        "title": "车规级芯片缺货价格暴涨，车企停产减产、交付延期并推高车价",
        "source_url": "https://wap.stockstar.com/detail/IG2026070300022323",
        "events": [
            ev("E001", "芯片缺货", "车规级芯片缺货", "经济/涨跌", 0.92),
            ev("E002", "芯片涨价", "车规芯片价格暴涨", "经济/涨跌", 0.88),
            ev("E003", "停产", "车企停产减产", "经济/涨跌", 0.90),
            ev("E004", "交付延期", "汽车交付延期", "社会/舆情", 0.86),
            ev("E005", "汽车涨价", "汽车价格上涨", "经济/涨跌", 0.85),
        ],
        "relations": [
            rel("R001", "E001", "E002", "缺货导致芯片涨价", "causal", 0.85),
            rel("R002", "E001", "E003", "缺货导致车企停产", "causal", 0.90),
            rel("R003", "E002", "E005", "芯片涨价推高汽车价格", "causal", 0.78),
            rel("R004", "E003", "E004", "停产导致交付延期", "causal", 0.90),
            rel("R005", "E004", "E005", "交付延期导致汽车涨价", "causal", 0.80),
        ],
        "queries": [
            q("Q1", "是什么导致了汽车价格上涨？", QT_CAUSAL_TRACING),
            q("Q2", "车规芯片缺货可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如车企停产没有发生，汽车价格上涨还会发生吗？", QT_COUNTERFACTUAL),
        ],
    },
    {
        "news_id": "news_04", "domain": "能源·高温限电", "date": "2023-06",
        "title": "四川持续高温用电负荷激增，电力供应趋紧，全省限电致部分水泥厂停窑",
        "source_url": "https://www.163.com/dy/article/I9FIBCCR0534A4SC.html",
        "events": [
            ev("E001", "高温", "四川持续高温", "灾害/事故", 0.95),
            ev("E002", "用电负荷", "用电负荷激增", "经济/涨跌", 0.90),
            ev("E003", "供应趋紧", "电力供应趋紧", "经济/涨跌", 0.88),
            ev("E004", "限电", "全省限电措施", "政策/发布", 0.86),
            ev("E005", "停窑", "部分水泥厂限电停窑", "经济/涨跌", 0.84),
            ev("E006", "节电", "发布全省节电倡议", "政策/发布", 0.80),
            ev("E007", "产量下降", "水泥产量下降", "经济/涨跌", 0.82),
        ],
        "relations": [
            rel("R001", "E001", "E002", "高温推高用电负荷", "causal", 0.90),
            rel("R002", "E002", "E003", "负荷激增致供应趋紧", "causal", 0.88),
            rel("R003", "E003", "E004", "供应趋紧，实施限电", "causal", 0.85),
            rel("R004", "E003", "E006", "供应趋紧，发布节电倡议", "causal", 0.80),
            rel("R005", "E004", "E005", "限电导致水泥厂停窑", "causal", 0.82),
            rel("R006", "E005", "E007", "停窑导致水泥产量下降", "causal", 0.80),
        ],
        "queries": [
            q("Q1", "是什么导致了水泥厂停窑？", QT_CAUSAL_TRACING),
            q("Q2", "四川持续高温可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如限电措施没有发生，水泥产量下降还会发生吗？", QT_COUNTERFACTUAL),
        ],
    },
    {
        "news_id": "news_05", "domain": "自然灾害·山火", "date": "2024",
        "title": "美国西部山火：150万英亩过火，毒烟笼罩5州，6000人被勒令撤离",
        "source_url": "https://www.chineseherald.co.nz/news/entertainment-2/wildfires-rage-across-western-us/",
        "events": [
            ev("E001", "山火", "美国西部山火蔓延", "灾害/事故", 0.95),
            ev("E002", "过火", "150万英亩土地过火", "灾害/事故", 0.90),
            ev("E003", "毒烟", "毒烟笼罩5州", "灾害/事故", 0.88),
            ev("E004", "撤离", "6000人被勒令撤离", "社会/舆情", 0.85),
            ev("E005", "健康威胁", "公众健康受威胁", "社会/舆情", 0.82),
        ],
        "relations": [
            rel("R001", "E001", "E002", "山火致150万英亩过火", "causal", 0.90),
            rel("R002", "E001", "E003", "山火产生毒烟", "causal", 0.85),
            rel("R003", "E002", "E003", "过火面积大，毒烟蔓延", "causal", 0.80),
            rel("R004", "E003", "E004", "毒烟笼罩，居民撤离", "causal", 0.85),
            rel("R005", "E003", "E005", "毒烟威胁公众健康", "causal", 0.82),
        ],
        "queries": [
            q("Q1", "是什么导致了6000人被撤离？", QT_CAUSAL_TRACING),
            q("Q2", "美国西部山火可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如毒烟没有产生，公众健康受威胁还会发生吗？", QT_COUNTERFACTUAL),
        ],
    },
    {
        "news_id": "news_06", "domain": "自然灾害·山火", "date": "2023-06",
        "title": "加拿大山火烟雾覆盖北美，空气质量恶化威胁公众健康并取消户外活动",
        "source_url": "https://www.vietnam.vn/ja/khoi-chay-rung-tai-canada-bao-phu-bac-my-de-doa-suc-khoe-cong-dong",
        "events": [
            ev("E001", "山火", "加拿大山火持续", "灾害/事故", 0.95),
            ev("E002", "烟雾", "烟雾覆盖北美", "灾害/事故", 0.90),
            ev("E003", "空气质量", "空气质量恶化", "灾害/事故", 0.88),
            ev("E004", "健康威胁", "公众健康受威胁", "社会/舆情", 0.82),
            ev("E005", "户外活动", "户外活动取消", "社会/舆情", 0.80),
        ],
        "relations": [
            rel("R001", "E001", "E002", "山火烟雾覆盖北美", "causal", 0.90),
            rel("R002", "E002", "E003", "烟雾导致空气质量恶化", "causal", 0.85),
            rel("R003", "E003", "E004", "空气质量恶化威胁健康", "causal", 0.82),
            rel("R004", "E003", "E005", "空气质量恶化，取消户外活动", "causal", 0.78),
        ],
        "queries": [
            q("Q1", "是什么导致了公众健康受威胁？", QT_CAUSAL_TRACING),
            q("Q2", "加拿大山火可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如空气质量恶化没有发生，户外活动取消还会发生吗？", QT_COUNTERFACTUAL),
        ],
    },
    {
        "news_id": "news_07", "domain": "航运·供应链", "date": "2024",
        "title": "红海霍尔木兹危机迫使船只绕行，航程延长推高全球运费与供应链成本",
        "source_url": "https://future.cfi.cn/p20260820000047.html",
        "events": [
            ev("E001", "红海危机", "红海霍尔木兹航运危机", "灾害/事故", 0.92),
            ev("E002", "绕行", "船只绕行好望角", "经济/涨跌", 0.90),
            ev("E003", "航程延长", "运输时间延长", "经济/涨跌", 0.86),
            ev("E004", "运费上涨", "全球供应链运费成本激增", "经济/涨跌", 0.85),
            ev("E005", "成本上升", "供应链成本上升", "经济/涨跌", 0.82),
        ],
        "relations": [
            rel("R001", "E001", "E002", "危机迫使船只绕行", "causal", 0.90),
            rel("R002", "E002", "E003", "绕行致航程延长", "causal", 0.88),
            rel("R003", "E003", "E004", "航程延长推高运费", "causal", 0.85),
            rel("R004", "E004", "E005", "运费上涨推高供应链成本", "causal", 0.82),
        ],
        "queries": [
            q("Q1", "是什么导致了全球运费成本激增？", QT_CAUSAL_TRACING),
            q("Q2", "红海危机可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如船只绕行没有发生，供应链成本上升还会发生吗？", QT_COUNTERFACTUAL),
        ],
    },
    {
        "news_id": "news_08", "domain": "航运·港口罢工", "date": "2024",
        "title": "欧洲码头大罢工致六大港口停摆，约4万TEU货物滞留、供应链延误",
        "source_url": "https://news.sohu.com/a/1064965052_122014422",
        "events": [
            ev("E001", "罢工", "欧洲码头大罢工", "社会/舆情", 0.92),
            ev("E002", "港口停摆", "六大港口运营中断", "经济/涨跌", 0.90),
            ev("E003", "货物滞留", "约4万TEU货物滞留", "经济/涨跌", 0.88),
            ev("E004", "供应链延误", "供应链延误", "经济/涨跌", 0.85),
            ev("E005", "应急响应", "航运公司启动应急响应", "政策/发布", 0.80),
        ],
        "relations": [
            rel("R001", "E001", "E002", "罢工致港口停摆", "causal", 0.90),
            rel("R002", "E002", "E003", "港口停摆致货物滞留", "causal", 0.88),
            rel("R003", "E003", "E004", "货物滞留致供应链延误", "causal", 0.85),
            rel("R004", "E004", "E005", "延误触发应急响应", "causal", 0.82),
        ],
        "queries": [
            q("Q1", "是什么导致了供应链延误？", QT_CAUSAL_TRACING),
            q("Q2", "码头大罢工可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如港口停摆没有发生，应急响应还会启动吗？", QT_COUNTERFACTUAL),
        ],
    },
    {
        "news_id": "news_09", "domain": "农业·粮食", "date": "2024",
        "title": "超强厄尔尼诺引发极端天气致农作物减产，粮食供应风险加剧、全球食品涨价",
        "source_url": "https://finance.eastmoney.com/a/202609033864093645.html",
        "events": [
            ev("E001", "厄尔尼诺", "超强厄尔尼诺", "灾害/事故", 0.92),
            ev("E002", "极端天气", "干旱洪水等极端天气", "灾害/事故", 0.88),
            ev("E003", "减产", "农作物减产", "经济/涨跌", 0.86),
            ev("E004", "供应风险", "粮食供应风险加剧", "经济/涨跌", 0.84),
            ev("E005", "食品涨价", "全球食品价格上涨", "经济/涨跌", 0.82),
        ],
        "relations": [
            rel("R001", "E001", "E002", "厄尔尼诺引发极端天气", "causal", 0.90),
            rel("R002", "E002", "E003", "极端天气致农作物减产", "causal", 0.88),
            rel("R003", "E003", "E004", "减产加剧供应风险", "causal", 0.85),
            rel("R004", "E004", "E005", "供应风险推高食品价格", "causal", 0.82),
        ],
        "queries": [
            q("Q1", "是什么导致了全球食品价格上涨？", QT_CAUSAL_TRACING),
            q("Q2", "超强厄尔尼诺可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如农作物减产没有发生，全球食品价格上涨还会发生吗？", QT_COUNTERFACTUAL),
        ],
    },
    {
        "news_id": "news_10", "domain": "经济·通胀", "date": "2024",
        "title": "全球粮食供应风险加剧，食品价格升至2022年以来最高，通胀压力与购买力承压",
        "source_url": "https://www.9fzt.com/9fztgw_1_top/ec45e4bbf8b6d9d65d743539b7bd0aa5.html",
        "events": [
            ev("E001", "供应风险", "全球粮食供应风险加剧", "经济/涨跌", 0.90),
            ev("E002", "食品价格", "全球食品价格升至2022年以来最高", "经济/涨跌", 0.88),
            ev("E003", "通胀", "通胀压力上升", "经济/涨跌", 0.85),
            ev("E004", "购买力", "消费者购买力下降", "经济/涨跌", 0.80),
        ],
        "relations": [
            rel("R001", "E001", "E002", "供应风险推高食品价格", "causal", 0.88),
            rel("R002", "E002", "E003", "食品涨价加剧通胀", "causal", 0.85),
            rel("R003", "E003", "E004", "通胀致购买力下降", "causal", 0.80),
        ],
        "queries": [
            q("Q1", "是什么导致了通胀压力上升？", QT_CAUSAL_TRACING),
            q("Q2", "粮食供应风险加剧可能引发哪些后续？", QT_SITUATION_DEDUCTION),
            q("Q3", "假如食品价格没有上涨，消费者购买力还会下降吗？", QT_COUNTERFACTUAL),
        ],
    },
]


def run():
    os.makedirs(TESTSET_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    all_results = []
    report = ["# 真实新闻因果图谱推理 —— 测试集与结果对照\n",
              f"> 共 {len(NEWS)} 条新闻，每条 3 个问题（因果追溯 / 态势推演 / 反事实）。\n",
              "> 因果图由报道要点重建，置信度为演示赋值；答案均带证据链。\n"]

    for news in NEWS:
        # 落盘测试集
        ts_path = os.path.join(TESTSET_DIR, f"{news['news_id']}.json")
        with open(ts_path, "w", encoding="utf-8") as f:
            json.dump(news, f, ensure_ascii=False, indent=2)

        events = [Event.from_dict(e) for e in news["events"]]
        relations = [CausalRelation.from_dict(r) for r in news["relations"]]
        queries = [Query.from_dict(qq) for qq in news["queries"]]
        graph = build_graph(events, relations)

        report.append(f"\n## {news['news_id']} · {news['title']}\n")
        report.append(f"- 领域：{news['domain']} ｜ 时间：{news['date']}")
        report.append(f"- 来源：{news['source_url']}")
        report.append(f"- 图谱：{len(graph.nodes)} 节点 / {len(graph.edges)} 边")
        report.append("- 边（cause → effect）：")
        for e in graph.edges:
            report.append(f"  - `{e.cause_event_id} → {e.effect_event_id}` [{e.relation_type}] {e.evidence[0]}")

        news_result = {"news_id": news["news_id"], "title": news["title"],
                       "source_url": news["source_url"], "answers": []}
        for qq in queries:
            ans = answer_query(graph, qq)
            news_result["answers"].append({
                "query_id": qq.query_id, "question": qq.question,
                "question_type": qq.question_type, "answer_text": ans.answer_text,
                "evidence_chain": ans.evidence_chain, "confidence": ans.confidence,
                "metadata": ans.metadata,
            })
            report.append(f"\n**{qq.query_id} [{qq.question_type}]** {qq.question}")
            report.append("```")
            report.append(ans.answer_text)
            report.append(f"证据链={ans.evidence_chain} 置信度={ans.confidence}")
            report.append("```")

        all_results.append(news_result)

    with open(os.path.join(RESULTS_DIR, "results_all.json"), "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    with open(os.path.join(RESULTS_DIR, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")

    print(f"完成：测试集 {len(NEWS)} 条 -> {TESTSET_DIR}")
    print(f"结果 -> {RESULTS_DIR}/results_all.json 与 report.md")


if __name__ == "__main__":
    run()
