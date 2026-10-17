"""Shared data loading, splitting and metrics for the frame classifier experiments (task #38)."""

import io
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold

# Order matters: the index in this list is the class id used everywhere.
FRAME_TYPES = ["studio", "casual", "graphic", "document"]
IMAGE_SIZE = 224
SEED = 42


def load_records(dataset_dir: Path) -> list[dict]:
    """One record per unique photo (the same URI can appear under many barcodes)."""
    by_uri: dict[str, dict] = {}
    with open(dataset_dir / "dataset.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            rec = by_uri.setdefault(
                row["uri"],
                {
                    "uri": row["uri"],
                    "barcodes": set(),
                    "type": FRAME_TYPES.index(row["type"]),
                    "classes": row["classes"],
                    "is_negative": row["is_negative"],
                },
            )
            rec["barcodes"].add(row["barcode"])
    records = sorted(by_uri.values(), key=lambda r: r["uri"])
    present = [r for r in records if (dataset_dir / r["uri"]).exists()]
    if len(present) != len(records):
        print(f"warning: {len(records) - len(present)} photos from dataset.jsonl are missing in {dataset_dir / 'orig'}, skipped")
    records = present
    for rec in records:
        rec["barcodes"] = sorted(rec["barcodes"])
    return records


def _barcode_groups(records: list[dict]) -> np.ndarray:
    """Connected components of the photo<->barcode graph.

    Photos of the same product (or sharing a photo) must land in the same split,
    otherwise near-duplicate shots leak between train and test.
    """
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for rec in records:
        for barcode in rec["barcodes"]:
            parent[find("u:" + rec["uri"])] = find("b:" + barcode)
    roots = {r: i for i, r in enumerate(sorted({find("u:" + rec["uri"]) for rec in records}))}
    return np.array([roots[find("u:" + rec["uri"])] for rec in records])


def make_splits(records: list[dict]) -> np.ndarray:
    """Return an array of 'train' / 'val' / 'test' per record (~80/10/10, grouped by product)."""
    y = np.array([r["type"] for r in records])
    groups = _barcode_groups(records)
    split = np.full(len(records), "train", dtype=object)

    outer = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=SEED)
    rest_idx, test_idx = next(outer.split(np.zeros(len(y)), y, groups))
    split[test_idx] = "test"

    inner = StratifiedGroupKFold(n_splits=9, shuffle=True, random_state=SEED)
    _, val_rel = next(inner.split(np.zeros(len(rest_idx)), y[rest_idx], groups[rest_idx]))
    split[rest_idx[val_rel]] = "val"
    return split.astype(str)


def _load_one(path: Path, harmonize: bool) -> np.ndarray:
    with Image.open(path) as img:
        img = img.convert("RGB")
        if harmonize:
            # Negatives come from a different source (256px JPEGs). Bring every image to the same
            # size cap and one more JPEG pass so resolution/compression cannot give the source away.
            img.thumbnail((256, 256), Image.LANCZOS)
            img.info.clear()  # a 64 KB JPEG comment in one source photo makes the encoder fail
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=90)
            img = Image.open(buf).convert("RGB")
        # Squash to a square without cropping: banners and labels keep their edges.
        return np.asarray(img.resize((IMAGE_SIZE, IMAGE_SIZE), Image.BICUBIC))


def load_images_from_paths(paths: list[Path], cache: Path, harmonize: bool = False) -> np.ndarray:
    """uint8 array [N, 224, 224, 3]; decoded once and cached, shared by every model."""
    if cache.exists():
        cached = np.load(cache)
        if len(cached) == len(paths):
            return cached
    with ThreadPoolExecutor(max_workers=8) as pool:
        images = np.stack(list(pool.map(lambda p: _load_one(p, harmonize), paths)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache, images)
    return images


def load_images(dataset_dir: Path, records: list[dict], cache: Path) -> np.ndarray:
    return load_images_from_paths([dataset_dir / r["uri"] for r in records], cache)


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, labels: list[str]) -> dict:
    ids = list(range(len(labels)))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=ids, average="macro", zero_division=0)),
        "report": classification_report(
            y_true, y_pred, labels=ids, target_names=labels, digits=3, zero_division=0
        ),
        "confusion": confusion_matrix(y_true, y_pred, labels=ids).tolist(),
    }


def print_eval(title: str, result: dict) -> None:
    print(f"\n=== {title} ===")
    print(f"accuracy={result['accuracy']:.4f}  macro_f1={result['macro_f1']:.4f}")
    print(result["report"])
    print("confusion (rows=true, cols=pred):", result["confusion"])
