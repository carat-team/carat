"""SigLIP 2: zero-shot and linear probe for the frame type / "perfume or not" classifier (task #38).

Image embeddings are computed once and cached, so the zero-shot prompts and the
linear head can be iterated on without re-running the vision tower.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from transformers import AutoModel, AutoTokenizer

from common import FRAME_TYPES, evaluate, load_images, load_records, make_splits, print_eval

MODEL_NAME = "google/siglip2-base-patch16-224"

TYPE_PROMPTS = {
    "studio": [
        "a studio product photo of a perfume bottle on a plain white background",
        "a perfume box on a clean neutral background, no props",
    ],
    "casual": [
        "a photo of a perfume bottle in an everyday scene with props and surroundings",
        "a perfume bottle standing on a table or shelf next to other objects",
    ],
    "graphic": [
        "an advertising banner or infographic for a perfume with text and badges",
        "a perfume product image with overlaid design, captions and icons",
    ],
    "document": [
        "a flat photo or scan of a document, sheet of paper or sticker",
        "a close-up photo of a printed label with small text",
    ],
}

PERFUME_PROMPTS = ["a photo of a perfume bottle", "a photo of perfume packaging"]
NOT_PERFUME_PROMPTS = [
    "a photo of clothing",
    "a photo of food",
    "a photo of furniture",
    "a photo of electronics",
    "a photo of a person",
    "a photo of an animal",
    "a photo of a landscape",
]


def _as_tensor(feats) -> torch.Tensor:
    # transformers >= 5 returns a ModelOutput from get_*_features, older versions a tensor.
    return feats if isinstance(feats, torch.Tensor) else feats.pooler_output


@torch.no_grad()
def embed_images(model, images: np.ndarray, batch_size: int) -> np.ndarray:
    # SigLIP preprocessing for this checkpoint is plain resize + normalize with mean=std=0.5;
    # images are already resized to 224x224 by load_images.
    out = []
    for start in range(0, len(images), batch_size):
        batch = torch.from_numpy(images[start : start + batch_size]).permute(0, 3, 1, 2).float()
        batch = (batch / 255.0 - 0.5) / 0.5
        feats = _as_tensor(model.get_image_features(pixel_values=batch))
        out.append(torch.nn.functional.normalize(feats, dim=-1).numpy())
        print(f"\rembedded {min(start + batch_size, len(images))}/{len(images)}", end="", flush=True)
    print()
    return np.concatenate(out)


@torch.no_grad()
def embed_texts(model, tokenizer, prompts: list[str]) -> np.ndarray:
    # SigLIP was trained with fixed-length padding; any other padding hurts quality.
    tokens = tokenizer(prompts, padding="max_length", max_length=64, truncation=True, return_tensors="pt")
    feats = _as_tensor(model.get_text_features(**tokens))
    return torch.nn.functional.normalize(feats, dim=-1).numpy()


def zero_shot_scores(model, tokenizer, img: np.ndarray, prompts: dict[str, list[str]]) -> np.ndarray:
    """Per-class score = mean over that class's prompts of the cosine similarity."""
    cols = []
    for name in prompts:
        txt = embed_texts(model, tokenizer, prompts[name])
        cols.append((img @ txt.T).mean(axis=1))
    return np.stack(cols, axis=1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, required=True, help="folder with dataset.jsonl and orig/")
    parser.add_argument("--work-dir", type=Path, required=True, help="cache and results are written here")
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)

    records = load_records(args.dataset_dir)
    split = make_splits(records)
    y = np.array([r["type"] for r in records])
    images = load_images(args.dataset_dir, records, args.work_dir / "images_224.npy")

    model = AutoModel.from_pretrained(args.model).eval()
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    cache = args.work_dir / f"embeddings_{args.model.split('/')[-1]}.npy"
    if cache.exists():
        emb = np.load(cache)
    else:
        emb = embed_images(model, images, args.batch_size)
        np.save(cache, emb)

    train, val, test = (split == s for s in ("train", "val", "test"))
    results: dict = {"model": args.model, "split_sizes": {s: int((split == s).sum()) for s in ("train", "val", "test")}}

    # --- Frame type: zero-shot ---
    scores = zero_shot_scores(model, tokenizer, emb, TYPE_PROMPTS)
    zs = evaluate(y[test], scores[test].argmax(axis=1), FRAME_TYPES)
    print_eval("frame type / SigLIP 2 zero-shot (test)", zs)
    results["type_zero_shot"] = zs

    # --- Frame type: linear probe (C picked on val, then refit on train only) ---
    best_c, best_f1 = None, -1.0
    for c in (0.1, 0.3, 1, 3, 10, 30, 100):
        clf = LogisticRegression(C=c, max_iter=2000, class_weight="balanced")
        clf.fit(emb[train], y[train])
        f1 = evaluate(y[val], clf.predict(emb[val]), FRAME_TYPES)["macro_f1"]
        print(f"linear probe C={c}: val macro_f1={f1:.4f}")
        if f1 > best_f1:
            best_c, best_f1 = c, f1
    clf = LogisticRegression(C=best_c, max_iter=2000, class_weight="balanced").fit(emb[train], y[train])
    probe = evaluate(y[test], clf.predict(emb[test]), FRAME_TYPES)
    probe["C"] = best_c
    print_eval(f"frame type / SigLIP 2 linear probe C={best_c} (test)", probe)
    results["type_linear_probe"] = probe

    # --- Perfume / not perfume ---
    is_perfume = np.array([not r["is_negative"] for r in records])
    perfume_txt = embed_texts(model, tokenizer, PERFUME_PROMPTS)
    other_txt = embed_texts(model, tokenizer, NOT_PERFUME_PROMPTS)
    pos = (emb @ perfume_txt.T).max(axis=1)
    neg = (emb @ other_txt.T).max(axis=1)
    zs_pred = pos > neg
    results["perfume"] = {
        "n_positive": int(is_perfume.sum()),
        "n_negative": int((~is_perfume).sum()),
        "zero_shot_recall_on_positives": float(zs_pred[is_perfume].mean()),
    }
    print("\n=== perfume / not perfume ===")
    print(json.dumps(results["perfume"], indent=2))
    if (~is_perfume).sum() == 0:
        print("dataset has no negative examples: precision/recall of the 'not perfume' side cannot be measured")

    (args.work_dir / "siglip_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
