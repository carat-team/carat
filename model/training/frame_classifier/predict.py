"""Classify photos with the exported SigLIP 2 heads: frame type and perfume / not perfume.

Weights come from final_evaluation.py --export-dir (siglip2_*_head.safetensors + weights.json);
the SigLIP 2 backbone itself is downloaded from Hugging Face. Prints one JSON object per image.

The perfume head was trained on harmonized images (size cap 256 px + one JPEG pass, see common.py),
so the same preprocessing is applied before it; the frame type head was trained on plain resized images.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file
from transformers import AutoModel

from common import _load_one
from siglip_experiment import embed_images


def softmax(logits: np.ndarray) -> np.ndarray:
    e = np.exp(logits - logits.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights-dir", type=Path, required=True)
    parser.add_argument("images", type=Path, nargs="+")
    args = parser.parse_args()

    manifest = json.loads((args.weights_dir / "weights.json").read_text())
    frame_head = load_file(args.weights_dir / "siglip2_frame_type_head.safetensors")
    perfume_head = load_file(args.weights_dir / "siglip2_perfume_head.safetensors")
    model = AutoModel.from_pretrained(manifest["backbone"]).eval()

    plain = embed_images(model, np.stack([_load_one(p, harmonize=False) for p in args.images]), 32)
    harmonized = embed_images(model, np.stack([_load_one(p, harmonize=True) for p in args.images]), 32)
    frame_probs = softmax(plain @ frame_head["weight"].T + frame_head["bias"])
    perfume_score = (harmonized @ perfume_head["weight"].T + perfume_head["bias"])[:, 0]

    for path, probs, score in zip(args.images, frame_probs, perfume_score):
        print(json.dumps({
            "image": str(path),
            "frame_type": manifest["frame_types"][int(probs.argmax())],
            "frame_type_probs": {t: round(float(p), 4) for t, p in zip(manifest["frame_types"], probs)},
            "perfume_score": round(float(score), 4),
            "is_perfume": bool(score >= manifest["perfume_threshold"]),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
