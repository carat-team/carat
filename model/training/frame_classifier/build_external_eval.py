"""Build a same-source external test set from the Fashion Product Images dataset (Marqo/KAGL on Hugging Face).

Perfume positives and non-perfume negatives come from one store, so a model cannot separate them by
photo style or resolution. It tests whether a classifier trained on the perfume photos + ABO negatives
looks at content rather than at which source an image came from. Images are for local evaluation only.

Positives: category3 in {"Perfume and Body Mist", "Fragrance Gift Set"}.
Negatives: a random sample of every other row except deodorants (ambiguous with fragrance).

Input: downloaded parquet shards (https://huggingface.co/datasets/Marqo/KAGL/tree/main/data).
Output (in --out-dir): external.jsonl (is_negative flag, source categories) + images/*.jpg.
"""

import argparse
import json
import random
from pathlib import Path

import pyarrow.parquet as pq

POSITIVE_TYPES = {"Perfume and Body Mist", "Fragrance Gift Set"}
SKIP_TYPES = {"Deodorant"}
COLUMNS = ["image", "category1", "category2", "category3", "item_ID"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shards", type=Path, nargs="+", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--negatives", type=int, default=600)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    (args.out_dir / "images").mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    positives, negatives = [], []  # (shard, row group, row, meta)
    for shard in args.shards:
        try:
            pf = pq.ParquetFile(shard)
        except Exception as e:  # a failed download leaves an HTML/text stub
            print(f"skip {shard.name}: {e}")
            continue
        for rg in range(pf.num_row_groups):
            meta = pf.read_row_group(rg, columns=COLUMNS[1:]).to_pylist()
            for i, m in enumerate(meta):
                if m["category3"] in POSITIVE_TYPES or m["category2"] == "Perfumes":
                    positives.append((shard, rg, i, m))
                elif m["category2"] != "Fragrance" and m["category3"] not in SKIP_TYPES:
                    negatives.append((shard, rg, i, m))
    rng.shuffle(negatives)
    chosen = [(*p, False) for p in positives] + [(*n, True) for n in negatives[: args.negatives]]
    print(f"{len(positives)} positives, {len(chosen) - len(positives)} negatives (of {len(negatives)} available)")

    by_group: dict[tuple[Path, int], list] = {}
    for shard, rg, i, m, neg in chosen:
        by_group.setdefault((shard, rg), []).append((i, m, neg))
    with open(args.out_dir / "external.jsonl", "w", encoding="utf-8") as out:
        for (shard, rg), items in by_group.items():
            rows = ParquetRows(shard, rg)
            for i, m, neg in items:
                name = f"{m['item_ID']}.jpg"
                (args.out_dir / "images" / name).write_bytes(rows.image_bytes(i))
                out.write(json.dumps({
                    "uri": f"images/{name}", "is_negative": neg, "source": "kagl",
                    "category1": m["category1"], "category2": m["category2"], "category3": m["category3"],
                }, ensure_ascii=False) + "\n")


class ParquetRows:
    def __init__(self, shard: Path, row_group: int):
        self.images = pq.ParquetFile(shard).read_row_group(row_group, columns=["image"]).column("image")

    def image_bytes(self, i: int) -> bytes:
        return self.images[i].as_py()["bytes"]


if __name__ == "__main__":
    main()
