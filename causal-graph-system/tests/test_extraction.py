"""模块1 · 训练负样本修复与 PAI 推理接入的测试。"""
import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _FakeTokenizer:
    """最小 tokenizer：每个字符一个 token，[CLS] 在 0，[SEP] 在末尾。"""

    pad_token_id = 0

    def __call__(self, text, **kwargs):
        n = len(text)
        input_ids = [1] * (n + 2)
        attention_mask = [1] * (n + 2)
        offset_mapping = [(0, 0)] + [(i, i + 1) for i in range(n)] + [(0, 0)]
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "offset_mapping": offset_mapping,
        }


def _load_train_extraction():
    path = os.path.join(ROOT, "scripts", "train_extraction.py")
    spec = importlib.util.spec_from_file_location("train_extraction", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_samples_generates_negative_samples():
    """修复点：无该论元的 (事件, 角色) 应生成负样本(start=end=[CLS])，而非被丢弃。"""
    te = _load_train_extraction()
    rows = [{
        "text": "雀巢裁员4000人",
        "events": [{
            "mapped_type": "经济/涨跌",
            "trigger": {"start": 2, "end": 4, "text": "裁员"},
            "arguments": [
                {"mapped_role": "object", "start": 4, "end": 9, "text": "4000人"},
            ],
        }],
    }]
    samples = te.build_samples(rows, _FakeTokenizer(), max_len=256)

    # trigger + 7 个通用角色 = 8 个样本
    assert len(samples) == 8

    pos = [s for s in samples if s["start_label"] != 0 or s["end_label"] != 0]
    neg = [s for s in samples if s["start_label"] == 0 and s["end_label"] == 0]
    # 正样本：trigger、object；负样本：其余 6 个角色
    assert len(pos) == 2
    assert len(neg) == 6


def test_extract_pai_missing_model_raises():
    """PAI 接入：未提供权重时应给出清晰报错，而非静默失败。"""
    from src.extraction.event_extractor import extract_events

    with pytest.raises(FileNotFoundError):
        extract_events([], {"model": "pai", "model_path": "no_such_file.pt"})
