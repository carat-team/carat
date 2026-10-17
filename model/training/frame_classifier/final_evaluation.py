"""Final comparison for task #38 with confidence intervals, and export of the trained heads.

Re-uses everything cached by the other scripts (no retraining of EfficientNet-B0):
  - frame type: SigLIP 2 zero-shot vs linear probe vs EfficientNet-B0 on the test split, bootstrap 95% CIs,
    paired bootstrap differences and McNemar's exact test;
  - perfume / not perfume: bootstrap CIs on the main test split and on the same-source external set.
Writes results/final_evaluation.json and, with --export-dir, the weights to publish
(SigLIP 2 heads as safetensors, EfficientNet-B0 state dicts) together with weights.json.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import torch
from safetensors.numpy import save_file
from scipy.stats import binomtest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from torchvision import models
from transformers import AutoModel, AutoTokenizer

from common import FRAME_TYPES, load_images_from_paths, load_records, make_splits
from efficientnet_baseline import predict
from evaluate_external import compute_scores
from siglip_experiment import MODEL_NAME, TYPE_PROMPTS, embed_images, embed_texts, zero_shot_scores

N_BOOT = 2000
FRAME_PROBE_C = 30  # picked on val in siglip_experiment.py
PERFUME_THRESHOLD = 0.0  # decision boundary of the class-balanced logistic regression, see README


def ci(values: np.ndarray) -> list[float]:
    low, high = np.percentile(values, [2.5, 97.5])
    return [round(float(low), 4), round(float(high), 4)]


def macro_f1(y: np.ndarray, pred: np.ndarray) -> float:
    return float(f1_score(y, pred, labels=list(range(len(FRAME_TYPES))), average="macro", zero_division=0))


def frame_type_section(dataset_dir: Path, work_dir: Path, model_name: str, export_dir: Path | None) -> dict:
    records = load_records(dataset_dir)
    split = make_splits(records)
    y = np.array([r["type"] for r in records])
    train, test = np.where(split == "train")[0], np.where(split == "test")[0]
    images = load_images_from_paths([dataset_dir / r["uri"] for r in records], work_dir / "images_224.npy")
    emb = np.load(work_dir / f"embeddings_{model_name.split('/')[-1]}.npy")

    model = AutoModel.from_pretrained(model_name).eval()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    preds = {"siglip2_zero_shot": zero_shot_scores(model, tokenizer, emb, TYPE_PROMPTS)[test].argmax(1)}
    probe = LogisticRegression(C=FRAME_PROBE_C, max_iter=2000, class_weight="balanced").fit(emb[train], y[train])
    preds["siglip2_linear_probe"] = probe.predict(emb[test])
    effnet = models.efficientnet_b0(weights=None)
    effnet.classifier[1] = torch.nn.Linear(effnet.classifier[1].in_features, len(FRAME_TYPES))
    effnet.load_state_dict(torch.load(work_dir / "efficientnet_b0_frame_type.pth"))
    preds["efficientnet_b0"] = predict(effnet, images, test)

    rng = np.random.default_rng(0)
    boots = rng.integers(0, len(test), size=(N_BOOT, len(test)))  # shared resamples -> paired comparisons
    yt = y[test]
    acc = {m: np.array([(p[b] == yt[b]).mean() for b in boots]) for m, p in preds.items()}
    f1 = {m: np.array([macro_f1(yt[b], p[b]) for b in boots]) for m, p in preds.items()}
    out: dict = {"n_test": int(len(test)), "models": {}, "paired": {}}
    for m, p in preds.items():
        out["models"][m] = {
            "accuracy": round(float((p == yt).mean()), 4), "accuracy_ci95": ci(acc[m]),
            "macro_f1": round(macro_f1(yt, p), 4), "macro_f1_ci95": ci(f1[m]),
        }
    for a, b in (("efficientnet_b0", "siglip2_linear_probe"), ("siglip2_linear_probe", "siglip2_zero_shot")):
        only_a = int(((preds[a] == yt) & (preds[b] != yt)).sum())
        only_b = int(((preds[a] != yt) & (preds[b] == yt)).sum())
        out["paired"][f"{a}_minus_{b}"] = {
            "accuracy_diff_ci95": ci(acc[a] - acc[b]), "macro_f1_diff_ci95": ci(f1[a] - f1[b]),
            "only_first_correct": only_a, "only_second_correct": only_b,
            "mcnemar_exact_p": round(float(binomtest(min(only_a, only_b), only_a + only_b, 0.5).pvalue), 4),
        }

    if export_dir is not None:
        # The head is a plain linear layer on the L2-normalised SigLIP 2 image embedding.
        # safetensors reads buffers as C-ordered: make the arrays contiguous (sklearn's coef_ can be F-ordered).
        save_file(
            {"weight": np.ascontiguousarray(probe.coef_, dtype=np.float32), "bias": np.ascontiguousarray(probe.intercept_, dtype=np.float32)},
            export_dir / "siglip2_frame_type_head.safetensors",
        )
        shutil.copy(work_dir / "efficientnet_b0_frame_type.pth", export_dir / "efficientnet_b0_frame_type.pth")
    return out


def bootstrap_binary(y: np.ndarray, scores: dict[str, np.ndarray], thresholds: dict[str, float]) -> dict:
    rng = np.random.default_rng(0)
    boots = rng.integers(0, len(y), size=(N_BOOT, len(y)))
    out = {}
    for name, score in scores.items():
        t = thresholds[name]
        pred = score >= t
        aucs, recalls, fprs = [], [], []
        for b in boots:
            yb, sb, pb = y[b], score[b], pred[b]
            aucs.append(roc_auc_score(yb, sb))
            recalls.append(pb[yb == 1].mean())
            fprs.append(pb[yb == 0].mean())
        out[name] = {
            "threshold": round(float(t), 4),
            "roc_auc": round(float(roc_auc_score(y, score)), 4), "roc_auc_ci95": ci(np.array(aucs)),
            "recall": round(float(pred[y == 1].mean()), 4), "recall_ci95": ci(np.array(recalls)),
            "fpr": round(float(pred[y == 0].mean()), 4), "fpr_ci95": ci(np.array(fprs)),
        }
    return out


def perfume_section(work_dir: Path, external_dir: Path, model_name: str, export_dir: Path | None) -> dict:
    main_results = json.loads((work_dir / "perfume_results.json").read_text())
    sc = np.load(work_dir / "perfume_scores.npz", allow_pickle=True)
    test = sc["split"] == "test"
    probe = torch.load(work_dir / "siglip2_perfume_probe.pt", weights_only=False)
    # name -> (score key in perfume_scores.npz, score key in external_scores.npz, threshold)
    entries = {
        "siglip2_zero_shot": ("siglip2_zero_shot_untuned_threshold", "siglip2_zero_shot", 0.0),  # prompts only, no data used
        "siglip2_zero_shot_val_threshold": (
            "siglip2_zero_shot_val_threshold", "siglip2_zero_shot", main_results["siglip2_zero_shot_val_threshold"]["all"]["threshold"]
        ),
        "siglip2_linear_probe": ("siglip2_linear_probe", "siglip2_linear_probe", PERFUME_THRESHOLD),
        "siglip2_linear_probe_val_threshold": (
            "siglip2_linear_probe", "siglip2_linear_probe", main_results["siglip2_linear_probe"]["all"]["threshold"]
        ),
        "efficientnet_b0": ("efficientnet_b0", "efficientnet_b0", 0.5),  # natural probability cut-off
        "efficientnet_b0_val_threshold": (
            "efficientnet_b0", "efficientnet_b0", main_results["efficientnet_b0"]["all"]["threshold"]
        ),
    }
    thr = {name: t for name, (_, _, t) in entries.items()}
    out = {"main_test": bootstrap_binary(sc["y"][test], {n: sc[k][test] for n, (k, _, _) in entries.items()}, thr)}
    out["main_test_n"] = {"positive": int((sc["y"][test] == 1).sum()), "negative": int((sc["y"][test] == 0).sum())}

    ext = np.load(work_dir / "external_scores.npz")
    out["external"] = bootstrap_binary(ext["y"], {n: ext[k] for n, (_, k, _) in entries.items()}, thr)
    out["external_n"] = {"positive": int(ext["y"].sum()), "negative": int((ext["y"] == 0).sum())}

    if export_dir is not None:
        save_file(
            {"weight": np.ascontiguousarray(probe["coef"], dtype=np.float32).reshape(1, -1),
             "bias": np.ascontiguousarray(probe["intercept"], dtype=np.float32).reshape(-1)},
            export_dir / "siglip2_perfume_head.safetensors",
        )
        shutil.copy(work_dir / "efficientnet_b0_perfume.pth", export_dir / "efficientnet_b0_perfume.pth")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True, help="caches/models from the other scripts")
    parser.add_argument("--external-dir", type=Path, required=True)
    parser.add_argument("--export-dir", type=Path, help="write the weights to publish here")
    parser.add_argument("--results", type=Path, default=Path("results/final_evaluation.json"))
    parser.add_argument("--model", default=MODEL_NAME)
    args = parser.parse_args()
    if args.export_dir:
        args.export_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "frame_type": frame_type_section(args.dataset_dir, args.work_dir, args.model, args.export_dir),
        "perfume": perfume_section(args.work_dir, args.external_dir, args.model, args.export_dir),
    }
    args.results.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(json.dumps(results, ensure_ascii=False, indent=2))

    if args.export_dir:
        files = sorted(p for p in args.export_dir.iterdir() if p.suffix in {".safetensors", ".pth"})
        manifest = {
            "backbone": args.model,
            "frame_types": FRAME_TYPES,
            "perfume_threshold": PERFUME_THRESHOLD,
            "files": {p.name: {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files},
        }
        (args.export_dir / "weights.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
