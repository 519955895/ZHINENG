"""模块2 ML 打分器训练工具（用 CEC 标注数据或合并数据集训练因果分类器）。

支持两种后端：
  1. BERT 微调（需要 torch + transformers）：bert-base-chinese
  2. TF-IDF + LogisticRegression（需要 sklearn）：轻量备选

支持两种数据输入：
  a) --merged-data：直接读 {cause, effect, label} JSONL（合并数据集）
  b) --events + --gold-relations：从 CEC 事件+标注构造（旧模式）

用法：
    # 方式1：用合并数据集训练 BERT（推荐）
    python -m src.relation.train_ml_scorer \\
        --merged-data data/training/merged_causal.jsonl \\
        --output-dir data/models/merged_bert \\
        --backend bert --epochs 3

    # 方式2：用 CEC 数据训练（旧模式）
    python -m src.relation.train_ml_scorer \\
        --events data/cec/cec_events.jsonl \\
        --gold-relations data/cec/cec_gold_relations.jsonl \\
        --output-dir data/models/cec_causal_scorer \\
        --backend bert

    # sklearn 备选（无需 torch）
    python -m src.relation.train_ml_scorer \\
        --merged-data data/training/merged_causal.jsonl \\
        --output-dir data/models/merged_sklearn \\
        --backend sklearn

训练后通过 ml_scorer.create_ml_scorer(output_dir) 加载并注入 extract_relations。
"""
from __future__ import annotations

import argparse
import json
import os
import random
from typing import Any, Dict, List, Tuple

from ..common.io_utils import load_events, load_relations
from ..common.schemas import CausalRelation, Event
from ..common.logger import get_logger

log = get_logger("relation.train")

# 可选依赖检测
try:
    import torch
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )
    from torch.utils.data import Dataset

    _BERT_AVAILABLE = True
except ImportError:
    _BERT_AVAILABLE = False

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split
    import joblib

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


# ---------- 数据构造 ----------

def build_dataset(
    events: List[Event],
    gold_relations: List[CausalRelation],
    neg_ratio: float = 3.0,
    seed: int = 42,
) -> Tuple[List[Tuple[str, str]], List[int]]:
    """构造训练样本。

    正例：标注的因果对 (cause.mention, effect.mention)
    负例：同文档内未标注的事件对，随机采样（正:负 ≈ 1:neg_ratio）

    Returns:
        (pairs, labels): pairs 为 (cause_text, effect_text) 列表，labels 为 0/1
    """
    rng = random.Random(seed)
    evt_map = {e.event_id: e for e in events}
    gold_pairs = {(r.cause_event_id, r.effect_event_id) for r in gold_relations}

    # 按文档分组
    doc_events: Dict[str, List[Event]] = {}
    for e in events:
        doc_events.setdefault(e.doc_id, []).append(e)

    pairs: List[Tuple[str, str]] = []
    labels: List[int] = []

    # 收集所有候选负例
    all_neg: List[Tuple[str, str]] = []
    for doc_id, evts in doc_events.items():
        for i, e_a in enumerate(evts):
            for e_b in evts[i + 1:]:
                if (e_a.event_id, e_b.event_id) in gold_pairs:
                    pairs.append((e_a.mention, e_b.mention))
                    labels.append(1)
                elif (e_b.event_id, e_a.event_id) in gold_pairs:
                    pairs.append((e_b.mention, e_a.mention))
                    labels.append(1)
                else:
                    all_neg.append((e_a.mention, e_b.mention))

    n_pos = len(pairs)
    n_neg_target = int(n_pos * neg_ratio)
    if len(all_neg) > n_neg_target:
        sampled_neg = rng.sample(all_neg, n_neg_target)
    else:
        sampled_neg = all_neg

    for neg in sampled_neg:
        pairs.append(neg)
        labels.append(0)

    log.info("数据集：正例 %d，负例 %d（总 %d）", n_pos, len(sampled_neg), len(pairs))
    return pairs, labels


def load_merged_data(filepath: str) -> Tuple[List[Tuple[str, str]], List[int]]:
    """从合并数据集 JSONL 直接加载。

    每行格式: {"cause": "...", "effect": "...", "label": 0|1, ...}
    """
    pairs: List[Tuple[str, str]] = []
    labels: List[int] = []
    n_pos = 0
    n_neg = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cause = d.get("cause", "").strip()
            effect = d.get("effect", "").strip()
            label = d.get("label", 0)
            if not cause or not effect:
                continue
            pairs.append((cause, effect))
            labels.append(label)
            if label == 1:
                n_pos += 1
            else:
                n_neg += 1
    log.info("合并数据集：正例 %d，负例 %d（总 %d）", n_pos, n_neg, len(pairs))
    return pairs, labels


# ---------- BERT 后端 ----------

if _BERT_AVAILABLE:
    from torch.utils.data import Dataset

    class _CausalDataset(Dataset):
        def __init__(self, pairs, labels, tokenizer, max_length=128):
            self.pairs = pairs
            self.labels = labels
            self.tokenizer = tokenizer
            self.max_length = max_length

        def __len__(self):
            return len(self.pairs)

        def __getitem__(self, idx):
            cause, effect = self.pairs[idx]
            text = f"{cause} [SEP] {effect}"
            enc = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt",
            )
            item = {k: v.squeeze(0) for k, v in enc.items()}
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
            return item


def train_bert(
    pairs: List[Tuple[str, str]],
    labels: List[int],
    output_dir: str,
    model_name: str = "bert-base-chinese",
    epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    test_size: float = 0.2,
    seed: int = 42,
) -> Dict[str, Any]:
    """用 BERT 微调因果分类器。"""
    if not _BERT_AVAILABLE:
        raise ImportError("BERT 训练需要 torch + transformers")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log.info("BERT 训练：模型=%s, device=%s, epochs=%d, lr=%s", model_name, device, epochs, learning_rate)

    # 划分训练/验证集
    from sklearn.model_selection import train_test_split as _split
    train_pairs, val_pairs, train_labels, val_labels = _split(
        pairs, labels, test_size=test_size, random_state=seed, stratify=labels
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=2
    )
    model.to(device)

    train_ds = _CausalDataset(train_pairs, train_labels, tokenizer)
    val_ds = _CausalDataset(val_pairs, val_labels, tokenizer)

    training_args = TrainingArguments(
        output_dir=os.path.join(output_dir, "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        seed=seed,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
    )

    trainer.train()

    # 保存模型
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # 验证集指标
    eval_result = trainer.evaluate()
    log.info("验证集 loss: %.4f", eval_result.get("eval_loss", 0))

    # 简单预测验证集计算准确率
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for i in range(0, len(val_pairs), batch_size):
            batch_pairs = val_pairs[i:i + batch_size]
            batch_labels = val_labels[i:i + batch_size]
            texts = [f"{c} [SEP] {e}" for c, e in batch_pairs]
            enc = tokenizer(
                texts, truncation=True, max_length=128,
                padding=True, return_tensors="pt"
            ).to(device)
            logits = model(**enc).logits
            preds = logits.argmax(dim=-1).cpu().tolist()
            correct += sum(p == l for p, l in zip(preds, batch_labels))
            total += len(batch_labels)
    val_acc = correct / total if total else 0
    log.info("验证集准确率: %.4f", val_acc)

    return {
        "backend": "bert",
        "model_name": model_name,
        "val_accuracy": round(val_acc, 4),
        "eval_loss": round(eval_result.get("eval_loss", 0), 4),
        "n_train": len(train_pairs),
        "n_val": len(val_pairs),
    }


# ---------- sklearn 后端 ----------

def train_sklearn(
    pairs: List[Tuple[str, str]],
    labels: List[int],
    output_dir: str,
    test_size: float = 0.2,
    seed: int = 42,
) -> Dict[str, Any]:
    """用 TF-IDF + LogisticRegression 训练因果分类器。"""
    if not _SKLEARN_AVAILABLE:
        raise ImportError("sklearn 训练需要 scikit-learn + joblib")

    texts = [f"{c} [SEP] {e}" for c, e in pairs]
    X_train, X_val, y_train, y_val = train_test_split(
        texts, labels, test_size=test_size, random_state=seed, stratify=labels
    )

    vectorizer = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(2, 4), max_features=10000
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_val_vec = vectorizer.transform(X_val)

    clf = LogisticRegression(max_iter=1000, random_state=seed, class_weight="balanced")
    clf.fit(X_train_vec, y_train)

    val_pred = clf.predict(X_val_vec)
    val_acc = (val_pred == np.array(y_val)).mean()
    report = classification_report(y_val, val_pred, output_dict=True, zero_division=0)
    log.info("验证集准确率: %.4f", val_acc)
    log.info("验证集分类报告:\n%s", classification_report(y_val, val_pred, zero_division=0))

    # 保存
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(vectorizer, os.path.join(output_dir, "tfidf_vectorizer.joblib"))
    joblib.dump(clf, os.path.join(output_dir, "logistic_regression.joblib"))

    meta = {
        "backend": "sklearn",
        "val_accuracy": round(float(val_acc), 4),
        "val_precision_causal": round(report["1"]["precision"], 4) if "1" in report else 0,
        "val_recall_causal": round(report["1"]["recall"], 4) if "1" in report else 0,
        "val_f1_causal": round(report["1"]["f1-score"], 4) if "1" in report else 0,
        "n_train": len(X_train),
        "n_val": len(X_val),
    }
    with open(os.path.join(output_dir, "train_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


# ---------- 主流程 ----------

def main():
    parser = argparse.ArgumentParser(description="模块2 ML 打分器训练")
    parser.add_argument("--merged-data", help="合并数据集 JSONL 路径（含 cause/effect/label）")
    parser.add_argument("--events", help="事件 JSONL 路径（旧模式，需配合 --gold-relations）")
    parser.add_argument("--gold-relations", help="标注因果对 JSONL 路径（旧模式）")
    parser.add_argument("--output-dir", default="data/models/cec_causal_scorer", help="模型输出目录")
    parser.add_argument("--backend", choices=["bert", "sklearn", "auto"], default="auto",
                        help="训练后端：bert/sklearn/auto(auto 优先 bert)")
    parser.add_argument("--model-name", default="bert-base-chinese", help="BERT 模型名")
    parser.add_argument("--epochs", type=int, default=5, help="BERT 训练轮数")
    parser.add_argument("--batch-size", type=int, default=16, help="BERT batch size")
    parser.add_argument("--neg-ratio", type=float, default=3.0, help="负例:正例比例（仅旧模式）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--lr", type=float, default=2e-5, help="BERT 学习率")
    args = parser.parse_args()

    # 加载数据
    if args.merged_data:
        print(f"从合并数据集加载: {args.merged_data}")
        pairs, labels = load_merged_data(args.merged_data)
    elif args.events and args.gold_relations:
        print(f"从 CEC 事件+标注构造数据集...")
        events = load_events(args.events)
        gold_rels = load_relations(args.gold_relations)
        print(f"加载 {len(events)} 个事件，{len(gold_rels)} 条标注因果对")
        pairs, labels = build_dataset(events, gold_rels, neg_ratio=args.neg_ratio, seed=args.seed)
    else:
        print("ERROR: 需要 --merged-data 或 --events + --gold-relations")
        return

    print(f"总样本: {len(pairs)} 条")

    # 选择后端
    backend = args.backend
    if backend == "auto":
        backend = "bert" if _BERT_AVAILABLE else "sklearn"
    print(f"\n使用后端: {backend}")

    if backend == "bert":
        if not _BERT_AVAILABLE:
            print("ERROR: torch/transformers 不可用，无法使用 bert 后端。")
            print("请安装：pip install torch transformers")
            print("或使用 --backend sklearn")
            return
        result = train_bert(
            pairs, labels, args.output_dir,
            model_name=args.model_name,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
            seed=args.seed,
        )
    else:
        if not _SKLEARN_AVAILABLE:
            print("ERROR: scikit-learn 不可用，无法使用 sklearn 后端。")
            print("请安装：pip install scikit-learn joblib")
            return
        result = train_sklearn(pairs, labels, args.output_dir, seed=args.seed)

    print(f"\n=== 训练结果 ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print(f"\n模型已保存到: {args.output_dir}")


if __name__ == "__main__":
    main()
