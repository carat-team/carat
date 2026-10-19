"""Compare the speed of SigLIP 2 and EfficientNet-B0 on your machine.

Measures, separately: model loading, parameter count, image preprocessing (if you pass photos)
and the forward pass for several batch sizes (random 224x224 input: speed does not depend on the picture).
Then estimates the cost of one photo for both tasks (frame type + perfume), the way predict.py runs them.

Examples:
  python benchmark.py
  python benchmark.py photos_folder/ --batch-sizes 1 16 --threads 4
  python benchmark.py --device cuda
"""

import argparse
import json
import statistics
import time
from pathlib import Path

import torch
from transformers import AutoModel

from predict import IMAGE_SUFFIXES, load_efficientnet, load_image


def timed(fn, warmup: int, repeats: int, device: str) -> float:
    """Median seconds per call; warm-up calls are discarded, CUDA is synchronised around every call."""
    sync = torch.cuda.synchronize if device.startswith("cuda") else (lambda: None)
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(repeats):
        sync()
        start = time.perf_counter()
        fn()
        sync()
        times.append(time.perf_counter() - start)
    return statistics.median(times)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("images", type=Path, nargs="*", help="optional photos/folders to time preprocessing on")
    parser.add_argument("--weights-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--batch-sizes", type=int, nargs="+", default=[1, 8, 32])
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--threads", type=int, help="CPU threads (default: torch default)")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if args.threads:
        torch.set_num_threads(args.threads)
    manifest = json.loads((args.weights_dir / "weights.json").read_text())
    print(f"device={args.device}, threads={torch.get_num_threads()}, torch {torch.__version__}")

    start = time.perf_counter()
    siglip = AutoModel.from_pretrained(manifest["backbone"]).eval().to(args.device)
    siglip_load = time.perf_counter() - start
    start = time.perf_counter()
    eff_frame = load_efficientnet(args.weights_dir / "efficientnet_b0_frame_type.pth", 4, args.device)
    eff_perfume = load_efficientnet(args.weights_dir / "efficientnet_b0_perfume.pth", 2, args.device)
    eff_load = time.perf_counter() - start
    print(f"\nload time (weights already on disk): SigLIP 2 {siglip_load:.1f} s | 2 x EfficientNet-B0 {eff_load:.1f} s")
    print(f"parameters: SigLIP 2 image tower {sum(p.numel() for p in siglip.vision_model.parameters()) / 1e6:.1f} M"
          f" | EfficientNet-B0 {sum(p.numel() for p in eff_frame.parameters()) / 1e6:.1f} M per network")

    prep_plain = prep_harmonized = 0.0
    photos = [p for path in args.images for p in (sorted(q for q in path.rglob("*") if q.suffix.lower() in IMAGE_SUFFIXES)
                                                  if path.is_dir() else [path])][:20]
    if photos:
        prep_plain = timed(lambda: [load_image(p, False) for p in photos], 1, 3, "cpu") / len(photos)
        prep_harmonized = timed(lambda: [load_image(p, True) for p in photos], 1, 3, "cpu") / len(photos)
        print(f"\npreprocessing per photo ({len(photos)} photos): plain {prep_plain * 1000:.0f} ms,"
              f" harmonized {prep_harmonized * 1000:.0f} ms (same for both models)")

    @torch.no_grad()
    def run_siglip(x: torch.Tensor) -> None:
        siglip.get_image_features(pixel_values=x)

    @torch.no_grad()
    def run_eff(x: torch.Tensor) -> None:
        eff_frame(x)

    print("\nforward pass, median ms per image (lower is faster):")
    print(f"{'batch':>6} {'SigLIP 2, 1 pass':>18} {'EfficientNet-B0, 1 net':>24} {'SigLIP 2 / EffNet':>19}")
    per_image = {}
    for batch in args.batch_sizes:
        x = torch.randn(batch, 3, 224, 224, device=args.device)
        sig = timed(lambda: run_siglip(x), args.warmup, args.repeats, args.device) / batch * 1000
        eff = timed(lambda: run_eff(x), args.warmup, args.repeats, args.device) / batch * 1000
        per_image[batch] = (sig, eff)
        print(f"{batch:>6} {sig:>18.1f} {eff:>24.1f} {sig / eff:>18.1f}x")

    # Best per-image time over the tried batch sizes: a single big batch is the noisiest measurement.
    sig = min(v[0] for v in per_image.values())
    eff = min(v[1] for v in per_image.values())
    # predict.py: SigLIP 2 runs twice per photo (plain + harmonized input), EfficientNet-B0 has one network per task.
    sig_photo = 2 * sig + prep_plain * 1000 + prep_harmonized * 1000
    eff_photo = 2 * eff + prep_plain * 1000 + prep_harmonized * 1000
    note = "" if photos else " (forward pass only: pass photos to include preprocessing)"
    print(f"\nestimated per photo, both tasks, best batch size{note}:")
    print(f"  SigLIP 2        {sig_photo:7.0f} ms")
    print(f"  EfficientNet-B0 {eff_photo:7.0f} ms   -> {'EfficientNet-B0' if eff_photo < sig_photo else 'SigLIP 2'} is "
          f"{max(sig_photo, eff_photo) / min(sig_photo, eff_photo):.1f}x faster")


if __name__ == "__main__":
    main()
