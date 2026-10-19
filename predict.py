"""Run the exported classifiers on photos: frame type and "perfume or not".

Four models, all loaded from the folder with this script (weights.json lists the files):
  - SigLIP 2 base + linear head for frame type (studio / casual / graphic / document);
  - SigLIP 2 base + linear head for perfume / not perfume;
  - EfficientNet-B0 for frame type;
  - EfficientNet-B0 for perfume / not perfume.
By default all four run and are printed side by side; --models picks a subset.

The SigLIP 2 backbone (google/siglip2-base-patch16-224, ~1.5 GB) is downloaded from Hugging Face on first run.
Needs: torch, torchvision, transformers, pillow, numpy, safetensors (see requirements.txt).

Examples:
  python predict.py photo.jpg
  python predict.py photos_folder/ --json > result.jsonl
  python predict.py photo.jpg --models siglip2
"""

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from safetensors.numpy import load_file
from torchvision import models
from transformers import AutoModel

IMAGE_SIZE = 224
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
EFFICIENTNET_PERFUME_THRESHOLD = 0.5  # probability cut-off used in the evaluation
IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)


def collect_images(paths: list[Path]) -> list[Path]:
    found = []
    for path in paths:
        if path.is_dir():
            found.extend(sorted(p for p in path.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES))
        elif path.is_file():
            found.append(path)
        else:
            sys.exit(f"error: {path} does not exist")
    if not found:
        sys.exit("error: no images found (supported: " + ", ".join(sorted(IMAGE_SUFFIXES)) + ")")
    return found


def load_image(path: Path, harmonize: bool) -> np.ndarray:
    """uint8 [224, 224, 3]. The perfume models were trained on harmonized images
    (size cap 256 px + one JPEG pass); the frame type models on plainly resized ones."""
    with Image.open(path) as img:
        img = img.convert("RGB")
        if harmonize:
            img.thumbnail((256, 256), Image.LANCZOS)
            img.info.clear()
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=90)
            img = Image.open(buf).convert("RGB")
        return np.asarray(img.resize((IMAGE_SIZE, IMAGE_SIZE), Image.BICUBIC))


def verify_weights(weights_dir: Path, manifest: dict) -> None:
    for name, info in manifest["files"].items():
        path = weights_dir / name
        if not path.exists():
            sys.exit(f"error: {path} is missing. Re-download the weights folder (see README.md).")
        if hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
            sys.exit(f"error: {name} is corrupted (SHA-256 mismatch). Re-download it (see README.md).")


def softmax(logits: np.ndarray) -> np.ndarray:
    e = np.exp(logits - logits.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


@torch.no_grad()
def siglip_embeddings(model, images: np.ndarray, batch_size: int, device: str) -> np.ndarray:
    out = []
    for start in range(0, len(images), batch_size):
        batch = torch.from_numpy(images[start : start + batch_size]).permute(0, 3, 1, 2).float().to(device)
        feats = model.get_image_features(pixel_values=(batch / 255.0 - 0.5) / 0.5)
        feats = feats if isinstance(feats, torch.Tensor) else feats.pooler_output  # transformers >= 5 returns an object
        out.append(torch.nn.functional.normalize(feats, dim=-1).cpu().numpy())
    return np.concatenate(out)


def load_efficientnet(path: Path, n_classes: int, device: str) -> torch.nn.Module:
    net = models.efficientnet_b0(weights=None)
    net.classifier[1] = torch.nn.Linear(net.classifier[1].in_features, n_classes)
    net.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
    return net.eval().to(device)


@torch.no_grad()
def efficientnet_probs(net: torch.nn.Module, images: np.ndarray, batch_size: int, device: str) -> np.ndarray:
    out = []
    for start in range(0, len(images), batch_size):
        batch = torch.from_numpy(images[start : start + batch_size]).permute(0, 3, 1, 2).float() / 255.0
        batch = ((batch - IMAGENET_MEAN) / IMAGENET_STD).to(device)
        out.append(torch.softmax(net(batch), dim=1).cpu().numpy())
    return np.concatenate(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("images", type=Path, nargs="+", help="image files and/or folders with images")
    parser.add_argument("--weights-dir", type=Path, default=Path(__file__).resolve().parent,
                        help="folder with weights.json and the weight files (default: next to this script)")
    parser.add_argument("--models", choices=["all", "siglip2", "efficientnet"], default="all")
    parser.add_argument("--json", action="store_true", help="print one JSON object per image instead of a table")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--device", default="cpu", help="cpu (default) or cuda")
    parser.add_argument("--skip-verify", action="store_true", help="do not check SHA-256 of the weight files")
    args = parser.parse_args()

    manifest = json.loads((args.weights_dir / "weights.json").read_text())
    if not args.skip_verify:
        verify_weights(args.weights_dir, manifest)
    frame_types = manifest["frame_types"]
    paths = collect_images(args.images)
    plain = np.stack([load_image(p, harmonize=False) for p in paths])
    harmonized = np.stack([load_image(p, harmonize=True) for p in paths])

    results: dict[str, dict[str, dict]] = {}  # model -> task -> per-image outputs
    if args.models in ("all", "siglip2"):
        backbone = AutoModel.from_pretrained(manifest["backbone"]).eval().to(args.device)
        frame = load_file(args.weights_dir / "siglip2_frame_type_head.safetensors")
        perfume = load_file(args.weights_dir / "siglip2_perfume_head.safetensors")
        probs = softmax(siglip_embeddings(backbone, plain, args.batch_size, args.device) @ frame["weight"].T + frame["bias"])
        score = (siglip_embeddings(backbone, harmonized, args.batch_size, args.device) @ perfume["weight"].T + perfume["bias"])[:, 0]
        results["siglip2"] = {"frame": probs, "perfume": score}
    if args.models in ("all", "efficientnet"):
        probs = efficientnet_probs(load_efficientnet(args.weights_dir / "efficientnet_b0_frame_type.pth", len(frame_types), args.device),
                                   plain, args.batch_size, args.device)
        perfume = efficientnet_probs(load_efficientnet(args.weights_dir / "efficientnet_b0_perfume.pth", 2, args.device),
                                     harmonized, args.batch_size, args.device)[:, 1]
        results["efficientnet_b0"] = {"frame": probs, "perfume": perfume}

    labels = {"siglip2": "SigLIP 2", "efficientnet_b0": "EfficientNet-B0"}
    thresholds = {
        "siglip2": manifest["perfume_threshold"],
        "efficientnet_b0": manifest.get("efficientnet_perfume_threshold", EFFICIENTNET_PERFUME_THRESHOLD),
    }
    for i, path in enumerate(paths):
        record: dict = {"image": str(path)}
        for name, r in results.items():
            record[name] = {
                "frame_type": frame_types[int(r["frame"][i].argmax())],
                "frame_type_probs": {t: round(float(p), 4) for t, p in zip(frame_types, r["frame"][i])},
                ("perfume_score" if name == "siglip2" else "perfume_probability"): round(float(r["perfume"][i]), 4),
                "is_perfume": bool(r["perfume"][i] >= thresholds[name]),
            }
        if args.json:
            print(json.dumps(record, ensure_ascii=False))
            continue
        print(path)
        for name, r in results.items():
            out = record[name]
            value = out.get("perfume_score", out.get("perfume_probability"))
            shown = f"score {value:+.3f}" if name == "siglip2" else f"prob {value:.3f}"
            print(f"  {labels[name]:<15} frame type: {out['frame_type']:<8} ({max(out['frame_type_probs'].values()):.2f})"
                  f"   perfume: {'YES' if out['is_perfume'] else 'no ':<3} ({shown})")


if __name__ == "__main__":
    main()
