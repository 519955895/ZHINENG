"""配置加载测试。"""
import os

from src.common.config import load_config, resolve_path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_load_challenge_config():
    cfg = load_config(os.path.join(ROOT, "configs", "challenge.yaml"))
    assert cfg.get("mode") == "challenge"
    assert cfg.get("extraction.model") == "rule"
    # 点号路径不存在时返回默认值
    assert cfg.get("nope.deep.key", "default") == "default"


def test_resolve_path():
    p = resolve_path(ROOT, "data/raw/news.jsonl")
    assert os.path.isabs(p)
