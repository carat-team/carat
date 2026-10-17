"""Build a "not perfume" negative set from Amazon Berkeley Objects (ABO, CC BY 4.0).

The labelled perfume dataset contains only positives, so negatives come from ABO marketplace
product photos (256px "small" images):
  - hard negatives: cosmetics and personal care (bottles, tubes, jars that look like perfume);
  - easy negatives: everything else, capped per product type so phone cases do not dominate.
Listings whose text mentions anything fragrance-like (in any language) are dropped, because
ABO has no "perfume" type and a mislabelled negative would poison the evaluation.

Output (in --out-dir): negatives.jsonl in the dataset.jsonl schema (is_negative=true) plus negatives/*.jpg.

Inputs: abo-listings.tar and abo-images-small.tar from
https://amazon-berkeley-objects.s3.amazonaws.com/archives/
"""

import argparse
import csv
import gzip
import json
import random
import re
import tarfile
from collections import defaultdict
from pathlib import Path

HARD_TYPES = {
    "BEAUTY", "HEALTH_PERSONAL_CARE", "ABIS_BEAUTY", "SKIN_CLEANING_AGENT", "SKIN_MOISTURIZER", "SHAMPOO",
    "NAIL_POLISH", "SKIN_CLEANING_WIPE", "SKIN_EXFOLIANT", "SKIN_TREATMENT_MASK", "COSMETIC_POWDER",
    "SKIN_FOUNDATION_CONCEALER", "COSMETIC_CASE", "COSMETIC_BRUSH",
}
# Deliberately aggressive: deodorants, body sprays and oils are dropped too, to keep negatives clean.
FRAGRANCE_RX = re.compile(
    r"perfum|parfum|parfüm|profum|cologne|colonia|eau de|eau-de|fragran|fraganc|duft|aftershave|after shave|"
    r"toilette|\bedt\b|\bedp\b|odeur|aroma spray|body mist|body spray|deodor|incense|essential oil",
    re.IGNORECASE,
)
TEXT_FIELDS = ("item_name", "item_keywords", "bullet_point", "brand", "product_description", "style", "model_name")


def listing_text(listing: dict) -> str:
    return " ".join(str(x.get("value", "")) for field in TEXT_FIELDS for x in listing.get(field) or [])


def read_listings(listings_tar: Path) -> list[dict]:
    rows = []
    with tarfile.open(listings_tar) as tar:
        for member in tar:
            if member.name.endswith(".json.gz"):
                with gzip.open(tar.extractfile(member), "rt", encoding="utf-8") as f:
                    rows.extend(json.loads(line) for line in f)
    return rows


def select(rows: list[dict], n_hard: int, n_easy: int, per_type_cap: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    clean = [
        r for r in rows
        if r.get("main_image_id") and r.get("product_type") and not FRAGRANCE_RX.search(listing_text(r))
    ]
    hard = [r for r in clean if r["product_type"][0]["value"] in HARD_TYPES]
    by_type = defaultdict(list)
    for r in clean:
        if r["product_type"][0]["value"] not in HARD_TYPES:
            by_type[r["product_type"][0]["value"]].append(r)
    rng.shuffle(hard)
    easy = []
    for items in by_type.values():
        rng.shuffle(items)
        easy.extend(items[:per_type_cap])
    rng.shuffle(easy)
    return [dict(r, _bucket="hard") for r in hard[:n_hard]] + [dict(r, _bucket="easy") for r in easy[:n_easy]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abo-dir", type=Path, required=True, help="folder with the two ABO .tar archives")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--hard", type=int, default=1000)
    parser.add_argument("--easy", type=int, default=2000)
    parser.add_argument("--per-type-cap", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    chosen = select(read_listings(args.abo_dir / "listings.tar"), args.hard, args.easy, args.per_type_cap, args.seed)
    wanted = {r["main_image_id"]: r for r in chosen}

    (args.out_dir / "negatives").mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.abo_dir / "images-small.tar") as tar:
        members = {m.name: m for m in tar if m.isfile()}  # the tar is uncompressed, so lookups are random access
        with gzip.open(tar.extractfile(members["images/metadata/images.csv.gz"]), "rt", encoding="utf-8") as f:
            path_of = {row["image_id"]: "images/small/" + row["path"] for row in csv.DictReader(f)}
        for image_id in wanted:
            member = members.get(path_of.get(image_id, ""))
            if member is not None:
                (args.out_dir / "negatives" / f"{image_id}.jpg").write_bytes(tar.extractfile(member).read())

    with open(args.out_dir / "negatives.jsonl", "w", encoding="utf-8") as f:
        for image_id, r in wanted.items():
            if not (args.out_dir / "negatives" / f"{image_id}.jpg").exists():
                continue
            f.write(json.dumps({
                "barcode": r["item_id"], "uri": f"negatives/{image_id}.jpg", "angles": [], "classes": [],
                "type": None, "is_negative": True, "source": "abo",
                "product_type": r["product_type"][0]["value"], "bucket": r["_bucket"],
            }, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
