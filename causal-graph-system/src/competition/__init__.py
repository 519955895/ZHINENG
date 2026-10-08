"""赛题适配层：加载竞赛数据包（A/B/C 三档）并产出 gold 兼容的答案 JSON。

入口：
    load_pack(pack_dir)                  -> Pack（文档/事件/关系/问题）
    run_testset(input_dir, output_dir)   -> 批量跑分，逐包写答案 JSON
"""
from .dataset import Pack, detect_task, load_pack
from .runner import run_pack, run_testset

__all__ = ["Pack", "detect_task", "load_pack", "run_pack", "run_testset"]
