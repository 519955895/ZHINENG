"""竞赛批量跑分：扫描测试集目录 -> 逐包构建因果图 -> 答题 -> 输出答案 JSON。

输出（output_dir 下）：
    <数据包名>.json          逐包答案列表（与 gold/问答对_答案.json 同构）
    submit_answers.json      全部答案的扁平数组（主提交文件）
    run_summary.json         跑分统计（包数/题数/题型分布/拒答数）
"""
from __future__ import annotations

import json
import os
from collections import Counter
from typing import List, Optional, Tuple

from ..common.logger import get_logger
from ..graph import build_graph
from ..relation import extract_relations
from . import answering
from .dataset import QUESTIONS_FILE, Pack, load_pack
from .extraction import build_events

log = get_logger("competition")


def prepare_pack_graph(pack: Pack):
    """按档位准备事件与因果图：
    A 直接使用给定事件+关系；B 自行识别关系；C 先抽事件再识别关系。
    返回 (graph, events, relations)。
    """
    if pack.given_events:
        events = pack.events
    else:
        events = build_events(pack.docs, pack.label_hints)
        pack.events = events

    if pack.given_relations:
        relations = pack.relations
    else:
        relations = extract_relations(events)
        pack.relations = relations

    graph = build_graph(events, relations)
    return graph, events, relations


def run_pack(pack: Pack) -> Tuple[List[dict], object]:
    """对单个数据包完成 建图 -> 逐题作答，返回 (答案记录, 因果图)。"""
    graph, _, _ = prepare_pack_graph(pack)
    log.info("[%s档] %s：节点 %d，边 %d，问题 %d",
             pack.task, pack.pack_name, len(graph.nodes), len(graph.edges),
             len(pack.questions))
    doc_text = {d.doc_id: d.text for d in pack.docs}
    records = []
    for q in pack.questions:
        rec = answering.answer_one(graph, q, task=pack.task, doc_text=doc_text)
        records.append(rec)
    return records, graph


def find_pack_dirs(input_dir: str) -> List[str]:
    """递归找出所有含 问题.json 的数据包目录。"""
    packs = []
    for root, _dirs, files in os.walk(input_dir):
        if QUESTIONS_FILE in files:
            packs.append(root)
    return sorted(packs)


def _write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _to_submit(record: dict) -> dict:
    """内部 gold 兼容记录 -> 赛方提交格式。

    - answer: 答案文本，证据不足时为 "无法确定"；
    - evidence_chain: 主证据链（一维，取第一条链），无法确定时为空列表；
    - confidence: 数值置信度（0-1），无法确定时为 null。

    按赛方评分规则，无答案题必须输出 "无法确定" + null + [] 才能拿到
    置信度/拒答分（20分）。是否拒答按 (question_type, reasoning_type) 组合的
    训练集空链率决定：
      - question_type=unanswerable 默认拒答；
      - 但 distractor_robustness（干扰排除题）即使标 unanswerable，79% 有
        实质"排除干扰"答案与证据链，须正常作答；
      - conflicting/missing/unanswerable 类标 unanswerable 时空链率≥91%，拒答。
    内部逐包 <名>.json 仍保留引擎给出的完整答案用于调试。
    """
    qtype = record.get("question_type")
    rtype = record.get("reasoning_type")
    chains = record.get("evidence_chains") or []
    conf = record.get("confidence")

    should_refuse = (qtype == "unanswerable"
                     and rtype != "distractor_robustness")
    if should_refuse:
        # 按赛方评分口径：无答案题必须拒答，否则该题三项全丢
        main_chain, conf_out, answer = [], None, "无法确定"
    else:
        refuse = record.get("confidence_level") is None
        if refuse:
            main_chain, conf_out, answer = [], None, "无法确定"
        else:
            main_chain = list(chains[0]) if chains else []
            # 提交置信度按"题型×内部分"经验校准为答案正确的期望概率
            # （内部图边分与答案正确率脱钩，直接提交会丢掉置信度校准分）
            conf_out = answering.calibrated_confidence(
                record.get("reasoning_type"), conf)
            answer = record.get("answers") or "无法确定"
    return {
        "sample_id": record.get("sample_id"),
        "answer": answer,
        "evidence_chain": main_chain,
        "confidence": conf_out,
        "question_type": record.get("question_type"),
    }


def run_testset(input_dir: str, output_dir: str,
                task: Optional[str] = None,
                limit: Optional[int] = None) -> dict:
    """批量跑分主入口。

    Args:
        input_dir: 测试集目录（可含多层 A/B/C 子目录），或单个数据包目录。
        output_dir: 答案输出目录。
        task: 强制档位（A/B/C），None 表示按包内文件自动识别。
        limit: 仅跑前 N 个包（调试用）。
    """
    input_dir = os.path.abspath(input_dir)
    output_dir = os.path.abspath(output_dir)

    if os.path.isfile(os.path.join(input_dir, QUESTIONS_FILE)):
        pack_dirs = [input_dir]
    else:
        pack_dirs = find_pack_dirs(input_dir)
    if limit:
        pack_dirs = pack_dirs[:limit]

    if not pack_dirs:
        raise FileNotFoundError(f"在 {input_dir} 下未找到任何含 {QUESTIONS_FILE} 的数据包")

    all_records: List[dict] = []
    type_counter: Counter = Counter()
    refuse_counter = 0
    pack_stats = []

    for pdir in pack_dirs:
        pack = load_pack(pdir, task=task)
        records, graph = run_pack(pack)
        all_records.extend(records)
        type_counter.update(r["question_type"] for r in records)
        refuse_counter += sum(1 for r in records if r["confidence_level"] is None)

        out_path = os.path.join(output_dir, f"{pack.pack_name}.json")
        _write_json(out_path, records)

        pack_stats.append({
            "pack": pack.pack_name,
            "task": pack.task,
            "task_detected_by_files": pack.task,
            "questions": len(records),
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
            "output": out_path,
        })
        log.info("  -> 已写出 %s", out_path)

    # 主提交文件按赛方要求格式：answer 单数 / evidence_chain 单链一维 /
    # confidence 数值（无法确定时为 null）
    submit_records = [_to_submit(r) for r in all_records]
    submit_path = os.path.join(output_dir, "submit_answers.json")
    _write_json(submit_path, submit_records)

    summary = {
        "input_dir": input_dir,
        "pack_count": len(pack_dirs),
        "question_count": len(all_records),
        "question_types": dict(type_counter),
        "refuse_count": refuse_counter,
        "submit_file": submit_path,
        "packs": pack_stats,
    }
    _write_json(os.path.join(output_dir, "run_summary.json"), summary)
    log.info("=== 完成：%d 包 %d 题，拒答 %d；主提交文件 %s ===",
             len(pack_dirs), len(all_records), refuse_counter, submit_path)
    return summary
