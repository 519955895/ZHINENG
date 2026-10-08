#!/usr/bin/env python
"""竞赛端到端跑分入口：给定测试集目录，输出答案 JSON 文件。

用法（在 causal-graph-system 目录下运行）：
    # 1) 跑 A 档抽样集（30 包，给定事件+关系）
    py scripts/run_competition.py --input "data/数据集/抽样测试集_100/测试集A_基础" \
        --output data/output/测试集A

    # 2) 跑 B 档（50 包，给定事件、系统自行识别关系）
    py scripts/run_competition.py --input "data/数据集/测试集B_推理" \
        --output data/output/测试集B

    # 3) 跑 C 档（20 包，仅文档，系统自行抽取事件+关系）
    py scripts/run_competition.py --input "data/数据集/抽样测试集_100/测试集C_鲁棒" \
        --output data/output/测试集C

    # 4) 整个抽样集（A/B/C 子目录递归扫描）
    py scripts/run_competition.py --input "data/数据集/抽样测试集_100" \
        --output data/output/抽样100

    # 调试：只跑前 3 个包
    py scripts/run_competition.py --input <目录> --output <目录> --limit 3

输出：<output>/<包名>.json（逐包）+ submit_answers.json（主提交）+ run_summary.json
"""
from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from src.competition.runner import run_testset  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="因果链问答竞赛跑分：测试集 -> 答案 JSON")
    p.add_argument("--input", "-i", required=True,
                   help="测试集目录（含若干数据包，或直接是一个数据包目录）")
    p.add_argument("--output", "-o", default="data/output/competition",
                   help="答案输出目录（默认 data/output/competition）")
    p.add_argument("--task", choices=["A", "B", "C"], default=None,
                   help="强制档位；默认按包内文件自动识别（有事件+关系=A，有事件=B，仅文档=C）")
    p.add_argument("--limit", type=int, default=None, help="只跑前 N 个包（调试用）")
    args = p.parse_args()

    summary = run_testset(args.input, args.output, task=args.task, limit=args.limit)
    print(f"\n跑分完成：{summary['pack_count']} 个数据包，{summary['question_count']} 个问题")
    print(f"题型分布：{summary['question_types']}")
    print(f"拒答题目：{summary['refuse_count']}")
    print(f"主提交文件：{summary['submit_file']}")


if __name__ == "__main__":
    main()
