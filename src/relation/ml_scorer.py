"""模块2 可选 ML 打分器（BERT / sklearn 因果分类）。

设计原则：
  - 可选依赖：transformers + torch 或 scikit-learn 可用时启用
  - 不伪造输出：模型不可用时不生成假分数，由调用方回退到规则基线
  - 可插拔：extract_relations(ml_scorer=...) 注入即可覆盖规则打分

用法：
    from src.relation.ml_scorer import is_ml_available, create_ml_scorer

    scorer = create_ml_scorer("data/models/cec_causal_scorer")
    relations = extract_relations(events, ml_scorer=scorer)
"""
from __future__ import annotations

import os
from typing import List, Optional, Tuple

from ..common.logger import get_logger

log = get_logger("relation.ml")

# 可选依赖检测
try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    _BERT_AVAILABLE = True
except ImportError:
    _BERT_AVAILABLE = False

try:
    import joblib
    import numpy as np

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


def is_ml_available() -> bool:
    """检测 BERT 或 sklearn 后端是否至少有一个可用。"""
    return _BERT_AVAILABLE or _SKLEARN_AVAILABLE


def _detect_backend(model_path: str) -> Optional[str]:
    """检测模型目录的后端类型。

    BERT 模型目录包含 config.json；sklearn 模型目录包含 logistic_regression.joblib。
    """
    if not os.path.isdir(model_path):
        return None
    if os.path.exists(os.path.join(model_path, "logistic_regression.joblib")):
        return "sklearn"
    if os.path.exists(os.path.join(model_path, "config.json")):
        return "bert"
    return None


class BertCausalScorer:
    """BERT 因果关系分类打分器。

    输入两个事件的 mention，输出：
      - is_causal_prob: [0, 1]，是否存在因果关系的概率
      - relation_type: causal / enables / prevents / conditional / none

    模型需为序列分类模型，标签空间约定：
      0: none
      1: causal
      2: enables
      3: prevents
      4: conditional
    """

    LABEL_MAP = {0: "none", 1: "causal", 2: "enables", 3: "prevents", 4: "conditional"}

    def __init__(self, model_name: str = "bert-base-chinese", device: Optional[str] = None):
        if not _BERT_AVAILABLE:
            raise ImportError(
                "BERT 打分器需要 transformers 和 torch。"
                "请安装：pip install transformers torch"
                "或使用 sklearn 后端。"
            )

        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        log.info("加载 ML 模型: %s (device=%s)", model_name, self.device)

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def score(self, cause_mention: str, effect_mention: str) -> Tuple[float, str]:
        """对一对事件打分。

        Returns:
            (is_causal_prob, relation_type)
            is_causal_prob: 非 none 类别的概率和
            relation_type: 概率最高的非 none 类别，若 none 最高则返回 "none"
        """
        text = f"{cause_mention} [SEP] {effect_mention}"
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=128,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0].cpu().numpy()

        # none 类别概率
        none_prob = float(probs[0])
        # 因果类概率和
        causal_prob = float(1.0 - none_prob)

        # 选概率最高的类别
        best_label = int(probs.argmax())
        relation_type = self.LABEL_MAP.get(best_label, "none")

        return causal_prob, relation_type

    def score_batch(
        self, pairs: List[Tuple[str, str]], batch_size: int = 64
    ) -> List[Tuple[float, str]]:
        """批量打分：一次处理多个事件对，利用 GPU 并行。

        Args:
            pairs: [(cause_mention, effect_mention), ...]
            batch_size: 每批大小（GPU 显存不足时调小）

        Returns:
            [(prob, relation_type), ...] 与输入顺序一一对应
        """
        if not pairs:
            return []

        results: List[Tuple[float, str]] = []
        for start in range(0, len(pairs), batch_size):
            batch = pairs[start : start + batch_size]
            texts = [f"{c} [SEP] {e}" for c, e in batch]
            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding=True,
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()

            for i in range(len(batch)):
                none_prob = float(probs[i][0])
                causal_prob = float(1.0 - none_prob)
                best_label = int(probs[i].argmax())
                relation_type = self.LABEL_MAP.get(best_label, "none")
                results.append((causal_prob, relation_type))

        return results


class SklearnCausalScorer:
    """sklearn TF-IDF + LogisticRegression 因果打分器（轻量备选）。

    与 BertCausalScorer 接口一致：score(cause, effect) -> (prob, relation_type)
    """

    LABEL_MAP = {0: "none", 1: "causal"}

    def __init__(self, model_dir: str):
        if not _SKLEARN_AVAILABLE:
            raise ImportError(
                "sklearn 打分器需要 scikit-learn + joblib。"
                "请安装：pip install scikit-learn joblib"
            )
        self.model_dir = model_dir
        self.vectorizer = joblib.load(os.path.join(model_dir, "tfidf_vectorizer.joblib"))
        self.clf = joblib.load(os.path.join(model_dir, "logistic_regression.joblib"))
        log.info("加载 sklearn 因果打分器: %s", model_dir)

    def score(self, cause_mention: str, effect_mention: str) -> Tuple[float, str]:
        """对一对事件打分。

        Returns:
            (is_causal_prob, relation_type)
            relation_type 固定为 "causal"（sklearn 后端只做二分类）
        """
        text = f"{cause_mention} [SEP] {effect_mention}"
        vec = self.vectorizer.transform([text])
        prob = float(self.clf.predict_proba(vec)[0][1])
        relation_type = "causal" if prob >= 0.5 else "none"
        return prob, relation_type

    def score_batch(
        self, pairs: List[Tuple[str, str]]
    ) -> List[Tuple[float, str]]:
        """批量打分（sklearn 已是向量化实现，直接一次处理）。"""
        if not pairs:
            return []
        texts = [f"{c} [SEP] {e}" for c, e in pairs]
        vecs = self.vectorizer.transform(texts)
        probs = self.clf.predict_proba(vecs)
        results: List[Tuple[float, str]] = []
        for i in range(len(pairs)):
            prob = float(probs[i][1])
            relation_type = "causal" if prob >= 0.5 else "none"
            results.append((prob, relation_type))
        return results


def create_ml_scorer(model_path: str = "bert-base-chinese") -> Optional[object]:
    """工厂函数：根据模型路径自动检测后端并创建打分器。

    - 若 model_path 是本地目录且包含 sklearn 模型文件 → SklearnCausalScorer
    - 若 model_path 是本地目录且包含 config.json → BertCausalScorer
    - 否则视为 HuggingFace 模型名 → BertCausalScorer
    """
    if not is_ml_available():
        log.warning("ML 依赖不可用，回退到规则基线。")
        return None

    backend = _detect_backend(model_path)

    if backend == "sklearn":
        if not _SKLEARN_AVAILABLE:
            log.warning("sklearn 依赖不可用，回退到规则基线。")
            return None
        return SklearnCausalScorer(model_path)

    # bert 后端（本地目录或 HuggingFace 模型名）
    if not _BERT_AVAILABLE:
        log.warning("torch/transformers 不可用，回退到规则基线。")
        return None
    return BertCausalScorer(model_path)
