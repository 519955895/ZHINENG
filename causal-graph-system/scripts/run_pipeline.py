"""一键运行入口。

用法：
    python scripts/run_pipeline.py --config configs/challenge.yaml
"""
from __future__ import annotations

import argparse
import os
import sys

# 让脚本能直接以 `python scripts/run_pipeline.py` 运行，无需装包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.orchestrator import run  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="新闻事件因果图谱与推理系统 - 一键运行")
    p.add_argument("--config", required=True, help="三档配置之一：configs/{basic,reasoning,challenge}.yaml")
    args = p.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
