"""EfficientNet-B0 fine-tuning baseline for the frame type classifier (task #38)."""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torchvision import models
from torchvision.transforms import v2

from common import FRAME_TYPES, SEED, evaluate, load_images, load_records, make_splits, print_eval

MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)

# No horizontal flip: mirrored text on labels/banners is not a realistic variation.
AUGMENT = v2.Compose(
    [
        v2.RandomResizedCrop(224, scale=(0.7, 1.0), ratio=(0.9, 1.1), antialias=True),
        v2.ColorJitter(brightness=0.2, contrast=0.2),
    ]
)


def to_batch(images: np.ndarray, idx: np.ndarray, augment: bool) -> torch.Tensor:
    batch = torch.from_numpy(images[idx]).permute(0, 3, 1, 2).contiguous()
    if augment:
        batch = torch.stack([AUGMENT(img) for img in batch])
    return (batch.float() / 255.0 - MEAN) / STD


@torch.no_grad()
def predict(model: nn.Module, images: np.ndarray, idx: np.ndarray, batch_size: int = 64) -> np.ndarray:
    model.eval()
    out = [model(to_batch(images, idx[i : i + batch_size], False)).argmax(1).numpy() for i in range(0, len(idx), batch_size)]
    return np.concatenate(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, required=True, help="folder with dataset.jsonl and orig/")
    parser.add_argument("--work-dir", type=Path, required=True, help="image cache and results location")
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)

    records = load_records(args.dataset_dir)
    split = make_splits(records)
    y = np.array([r["type"] for r in records])
    images = load_images(args.dataset_dir, records, args.work_dir / "images_224.npy")
    train_idx, val_idx, test_idx = (np.where(split == s)[0] for s in ("train", "val", "test"))

    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(FRAME_TYPES))

    counts = np.bincount(y[train_idx], minlength=len(FRAME_TYPES))
    weights = torch.tensor(len(train_idx) / (len(FRAME_TYPES) * counts), dtype=torch.float32)
    loss_fn = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.05)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    steps = args.epochs * (len(train_idx) // args.batch_size)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=args.lr, total_steps=steps, pct_start=0.15)

    best_f1, best_state, history = -1.0, None, []
    for epoch in range(args.epochs):
        model.train()
        order = rng.permutation(train_idx)
        started, total = time.time(), 0.0
        for step in range(len(order) // args.batch_size):
            idx = order[step * args.batch_size : (step + 1) * args.batch_size]
            loss = loss_fn(model(to_batch(images, idx, True)), torch.from_numpy(y[idx]))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()
            total += loss.item()
        val = evaluate(y[val_idx], predict(model, images, val_idx), FRAME_TYPES)
        history.append({"epoch": epoch + 1, "train_loss": total / (step + 1), "val_macro_f1": val["macro_f1"]})
        print(f"epoch {epoch + 1}/{args.epochs} loss={total / (step + 1):.4f} val_acc={val['accuracy']:.4f} "
              f"val_macro_f1={val['macro_f1']:.4f} ({time.time() - started:.0f}s)", flush=True)
        if val["macro_f1"] > best_f1:
            best_f1 = val["macro_f1"]
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    result = evaluate(y[test_idx], predict(model, images, test_idx), FRAME_TYPES)
    result["history"] = history
    print_eval("frame type / EfficientNet-B0 fine-tuned (test)", result)
    (args.work_dir / "efficientnet_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    torch.save(best_state, args.work_dir / "efficientnet_b0_frame_type.pth")


if __name__ == "__main__":
    main()
