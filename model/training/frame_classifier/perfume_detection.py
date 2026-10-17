""""Perfume or not": SigLIP 2 (zero-shot, linear probe) vs EfficientNet-B0 on perfume + ABO negatives (task #38).

Positives: the labelled perfume photos. Negatives: build_negatives.py output (ABO product photos).
Every image goes through the same harmonization (size cap + JPEG pass) so the source is not leaked
by resolution. Zero-shot never sees the negatives; the trained heads do.
"""

import argparse
import io
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from transformers import AutoModel, AutoTokenizer

from common import SEED, load_images_from_paths, load_records, make_splits
from efficientnet_baseline import predict_proba, train
from siglip_experiment import MODEL_NAME, NOT_PERFUME_PROMPTS, PERFUME_PROMPTS, embed_images, embed_texts

# Second prompt set, written after seeing what the negatives look like (marketplace goods incl. cosmetics).
# Tuned by hand against val only; reported separately from the untouched first set.
NOT_PERFUME_PROMPTS_V2 = NOT_PERFUME_PROMPTS + [
    "a photo of a cosmetics or skincare product",
    "a photo of a shampoo or lotion bottle",
    "a photo of vitamins or a supplement bottle",
    "a photo of household cleaning products",
    "a photo of a product package on a white background",
    "a photo of shoes or a bag",
    "a photo of jewelry",
]


def split_negatives(n: int, buckets: list[str]) -> np.ndarray:
    idx = np.arange(n)
    rest, test = train_test_split(idx, test_size=0.1, random_state=SEED, stratify=buckets)
    train, val = train_test_split(rest, test_size=1 / 9, random_state=SEED, stratify=np.array(buckets)[rest])
    out = np.empty(n, dtype=object)
    out[train], out[val], out[test] = "train", "val", "test"
    return out.astype(str)


def metrics(y: np.ndarray, score: np.ndarray, threshold: float, bucket: np.ndarray) -> dict:
    """y=1 means perfume. score: higher = more perfume-like."""
    pred = score >= threshold
    tp, fn = int((pred & (y == 1)).sum()), int((~pred & (y == 1)).sum())
    fp, tn = int((pred & (y == 0)).sum()), int((~pred & (y == 0)).sum())
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    # Operational view: reject as many non-perfume photos as possible while keeping 99% of perfumes.
    pos_scores = np.sort(score[y == 1])
    t99 = pos_scores[int(0.01 * len(pos_scores))]
    result = {
        "roc_auc": float(roc_auc_score(y, score)),
        "pr_auc": float(average_precision_score(y, score)),
        "threshold": float(threshold),
        "accuracy": (tp + tn) / len(y),
        "balanced_accuracy": 0.5 * (recall + tn / max(tn + fp, 1)),
        "perfume_precision": precision,
        "perfume_recall": recall,
        "perfume_f1": 2 * precision * recall / max(precision + recall, 1e-9),
        "confusion": {"tp": tp, "fn": fn, "fp": fp, "tn": tn},
        "negatives_rejected_at_99pct_perfume_recall": float((score[y == 0] < t99).mean()),
    }
    for name in ("easy", "hard"):
        mask = (y == 0) & (bucket == name)
        result[f"false_positive_rate_{name}_negatives"] = float((score[mask] >= threshold).mean())
    return result


def best_f1_threshold(y: np.ndarray, score: np.ndarray) -> float:
    cands = np.unique(np.quantile(score, np.linspace(0.01, 0.99, 197)))
    f1 = []
    for t in cands:
        p = score >= t
        tp = (p & (y == 1)).sum()
        f1.append(2 * tp / max(p.sum() + (y == 1).sum(), 1))
    return float(cands[int(np.argmax(f1))])


def shortcut_features(images: np.ndarray) -> np.ndarray:
    """Trivial low-level cues; if these alone separate the classes, the benchmark is not trustworthy."""
    feats = []
    for img in images:
        g = img.mean(axis=2)
        buf = io.BytesIO()
        Image.fromarray(img).save(buf, "JPEG", quality=75)
        feats.append([
            *img.reshape(-1, 3).mean(0), g.std(), (g >= 250).mean(),
            np.abs(np.diff(g, axis=0)).mean(), np.abs(np.diff(g, axis=1)).mean(), len(buf.getvalue()),
        ])
    return np.array(feats)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, required=True, help="folder with dataset.jsonl and orig/")
    parser.add_argument("--negatives-dir", type=Path, required=True, help="build_negatives.py output")
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args()

    pos = load_records(args.dataset_dir)
    pos_split = make_splits(pos)
    neg = [json.loads(line) for line in open(args.negatives_dir / "negatives.jsonl", encoding="utf-8")]
    neg_split = split_negatives(len(neg), [r["bucket"] for r in neg])

    paths = [args.dataset_dir / r["uri"] for r in pos] + [args.negatives_dir / r["uri"] for r in neg]
    y = np.array([1] * len(pos) + [0] * len(neg))
    split = np.concatenate([pos_split, neg_split])
    bucket = np.array(["pos"] * len(pos) + [r["bucket"] for r in neg])
    images = load_images_from_paths(paths, args.work_dir / "images_224_binary.npy", harmonize=True)
    train_idx, val_idx, test_idx = (np.where(split == s)[0] for s in ("train", "val", "test"))
    print({s: {"pos": int(((split == s) & (y == 1)).sum()), "neg": int(((split == s) & (y == 0)).sum())}
           for s in ("train", "val", "test")})

    results: dict = {"sizes": {s: {"pos": int(((split == s) & (y == 1)).sum()), "neg": int(((split == s) & (y == 0)).sum())}
                                for s in ("train", "val", "test")}}

    def report(name: str, score: np.ndarray, threshold: float | None = None) -> None:
        t = best_f1_threshold(y[val_idx], score[val_idx]) if threshold is None else threshold
        m = metrics(y[test_idx], score[test_idx], t, bucket[test_idx])
        results[name] = m
        print(f"\n=== {name} (test) ===")
        print(json.dumps(m, indent=2))

    # --- shortcut check ---
    feats = shortcut_features(images)
    shortcut = HistGradientBoostingClassifier(random_state=SEED).fit(feats[train_idx], y[train_idx])
    results["shortcut_baseline_roc_auc"] = float(roc_auc_score(y[test_idx], shortcut.predict_proba(feats[test_idx])[:, 1]))
    print("\nshortcut baseline (low-level stats only) test ROC-AUC:", results["shortcut_baseline_roc_auc"])

    # --- SigLIP 2 ---
    model = AutoModel.from_pretrained(args.model).eval()
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    cache = args.work_dir / f"embeddings_binary_{args.model.split('/')[-1]}.npy"
    if cache.exists():
        emb = np.load(cache)
    else:
        emb = embed_images(model, images, 32)
        np.save(cache, emb)

    pos_txt = embed_texts(model, tokenizer, PERFUME_PROMPTS)
    for name, prompts in (("siglip2_zero_shot", NOT_PERFUME_PROMPTS), ("siglip2_zero_shot_prompts_v2", NOT_PERFUME_PROMPTS_V2)):
        neg_txt = embed_texts(model, tokenizer, prompts)
        score = (emb @ pos_txt.T).max(1) - (emb @ neg_txt.T).max(1)
        report(name + "_untuned_threshold", score, 0.0)  # "perfume wins" rule, no data used
        report(name + "_val_threshold", score)

    best_c, best_auc = 1.0, -1.0
    for c in (0.1, 0.3, 1, 3, 10, 30):
        clf = LogisticRegression(C=c, max_iter=3000, class_weight="balanced").fit(emb[train_idx], y[train_idx])
        auc = roc_auc_score(y[val_idx], clf.decision_function(emb[val_idx]))
        print(f"linear probe C={c}: val ROC-AUC={auc:.4f}")
        if auc > best_auc:
            best_c, best_auc = c, auc
    clf = LogisticRegression(C=best_c, max_iter=3000, class_weight="balanced").fit(emb[train_idx], y[train_idx])
    results["linear_probe_C"] = best_c
    report("siglip2_linear_probe", clf.decision_function(emb))
    torch.save({"coef": clf.coef_, "intercept": clf.intercept_}, args.work_dir / "siglip2_perfume_probe.pt")

    # --- EfficientNet-B0 ---
    def val_auc(m: torch.nn.Module) -> float:
        return float(roc_auc_score(y[val_idx], predict_proba(m, images, val_idx)[:, 1]))

    effnet, history = train(images, y, train_idx, 2, val_auc, args.epochs)
    results["efficientnet_history"] = history
    score = np.zeros(len(y))
    score[val_idx] = predict_proba(effnet, images, val_idx)[:, 1]
    score[test_idx] = predict_proba(effnet, images, test_idx)[:, 1]
    report("efficientnet_b0", score)
    torch.save(effnet.state_dict(), args.work_dir / "efficientnet_b0_perfume.pth")

    (args.work_dir / "perfume_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
