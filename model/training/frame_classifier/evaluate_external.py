"""Apply the models from perfume_detection.py to the same-source external set (build_external_eval.py).

Thresholds are taken from the main experiment (chosen on its val split), not re-tuned here, so the
numbers show how the models behave on data from a source they never saw.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import average_precision_score, roc_auc_score
from torchvision import models
from transformers import AutoModel, AutoTokenizer

from common import load_images_from_paths
from efficientnet_baseline import predict_proba
from perfume_detection import NOT_PERFUME_PROMPTS, NOT_PERFUME_PROMPTS_V2
from siglip_experiment import MODEL_NAME, PERFUME_PROMPTS, embed_images, embed_texts


def summarize(y: np.ndarray, score: np.ndarray, threshold: float) -> dict:
    pred = score >= threshold
    pos, neg = y == 1, y == 0
    return {
        "roc_auc": float(roc_auc_score(y, score)),
        "pr_auc": float(average_precision_score(y, score)),
        "threshold": float(threshold),
        "perfume_recall": float(pred[pos].mean()),
        "false_positive_rate": float(pred[neg].mean()),
        "accuracy": float((pred == pos).mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True, help="where perfume_detection.py wrote its results")
    parser.add_argument("--model", default=MODEL_NAME)
    args = parser.parse_args()

    rows = [json.loads(line) for line in open(args.external_dir / "external.jsonl", encoding="utf-8")]
    y = np.array([0 if r["is_negative"] else 1 for r in rows])
    images = load_images_from_paths(
        [args.external_dir / r["uri"] for r in rows], args.work_dir / "images_224_external.npy", harmonize=True
    )
    main_results = json.loads((args.work_dir / "perfume_results.json").read_text())

    def thr(name: str) -> float:
        return main_results[name]["all"]["threshold"]

    results = {"n_positive": int(y.sum()), "n_negative": int((y == 0).sum())}

    siglip = AutoModel.from_pretrained(args.model).eval()
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    emb = embed_images(siglip, images, 32)
    pos_txt = embed_texts(siglip, tokenizer, PERFUME_PROMPTS)
    for name, prompts in (("siglip2_zero_shot", NOT_PERFUME_PROMPTS), ("siglip2_zero_shot_prompts_v2", NOT_PERFUME_PROMPTS_V2)):
        score = (emb @ pos_txt.T).max(1) - (emb @ embed_texts(siglip, tokenizer, prompts).T).max(1)
        results[name + "_untuned_threshold"] = summarize(y, score, 0.0)
        results[name + "_val_threshold"] = summarize(y, score, thr(name + "_val_threshold"))

    probe = torch.load(args.work_dir / "siglip2_perfume_probe.pt", weights_only=False)
    score = emb @ probe["coef"].ravel() + probe["intercept"].ravel()[0]
    results["siglip2_linear_probe"] = summarize(y, score, thr("siglip2_linear_probe"))

    effnet = models.efficientnet_b0(weights=None)
    effnet.classifier[1] = torch.nn.Linear(effnet.classifier[1].in_features, 2)
    effnet.load_state_dict(torch.load(args.work_dir / "efficientnet_b0_perfume.pth"))
    score = predict_proba(effnet, images, np.arange(len(images)))[:, 1]
    results["efficientnet_b0"] = summarize(y, score, thr("efficientnet_b0"))

    for name, r in results.items():
        if isinstance(r, dict):
            print(f"{name:36s} auc={r['roc_auc']:.3f} recall={r['perfume_recall']:.3f} fpr={r['false_positive_rate']:.3f} acc={r['accuracy']:.3f}")
    (args.work_dir / "external_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
