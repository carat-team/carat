"""Build a name-grouped holdout, train and export from the customer's local data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import pandas as pd
from carat_algorithms.text.perfumery_type.model import PerfumeTypePredictor, normalize
from carat_algorithms.text.perfumery_type.rules import detect_types_in_name
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit

from model import PerfumeTypeModel

LABELS = {
    "ДУХИ": "ДУХИ",
    "ДЕТСКИЕ ДУХИ": "ДУХИ",
    "НАТУРАЛЬНЫЕ ТВЕРДЫЕ ДУХИ": "ДУХИ",
    "ПАРФЮМЕРНАЯ ВОДА": "ПАРФЮМЕРНАЯ ВОДА",
    "ПАРФЮМИРОВАННАЯ ВОДА": "ПАРФЮМЕРНАЯ ВОДА",
    "ТУАЛЕТНАЯ ВОДА": "ТУАЛЕТНАЯ ВОДА",
    "ОДЕКОЛОН": "ОДЕКОЛОН",
    "ДУШИСТАЯ ВОДА": "ДУШИСТАЯ ВОДА",
    "СПРЕЙ ДЛЯ ТЕЛА": "СПРЕЙ ДЛЯ ТЕЛА",
}
RULE_LABELS = {
    "духи": "ДУХИ",
    "твердые духи": "ДУХИ",
    "парфюмированная вода": "ПАРФЮМЕРНАЯ ВОДА",
    "туалетная вода": "ТУАЛЕТНАЯ ВОДА",
    "одеколон": "ОДЕКОЛОН",
    "мист": "СПРЕЙ ДЛЯ ТЕЛА",
    "парфюмерный спрей": "СПРЕЙ ДЛЯ ТЕЛА",
}


def weak_label(text: str) -> str | None:
    if re.search(r"\b(?:мотив\w*|inspired|реплик\w*|аналог\w*|набор\w*|комплект\w*)", normalize(text)):
        return None
    found = detect_types_in_name(text)
    return RULE_LABELS.get(found[0]) if len(found) == 1 else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    args = parser.parse_args()
    source = next(args.data_dir.glob("ТГ Парфюмерия*все атрибуты*.xlsx"))
    attrs = pd.read_excel(source, dtype=str, keep_default_na=False)
    attrs.columns = [re.sub(r"\s*\(\d+\)", "", column).strip() for column in attrs.columns]
    attrs = attrs.rename(
        columns={"Полное наименование товара": "name", "Тип парфюмерии": "declared", "Код товара": "code"}
    )
    attrs["label"] = attrs["declared"].str.strip().str.upper().str.replace("Ё", "Е").map(LABELS)
    attrs["norm"] = attrs["name"].map(normalize)
    work = attrs[(attrs["norm"] != "") & attrs["label"].notna()].reset_index(drop=True)
    fit_indices, test_indices = next(
        GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42).split(work, groups=work["norm"])
    )
    fit, test = work.iloc[fit_indices], work.iloc[test_indices]
    pool = pd.read_csv(
        args.data_dir / "perfumery_brands.csv", dtype=str, keep_default_na=False, usecols=["barcode", "text"]
    )
    pool = pool[(pool["text"].str.strip() != "") & ~pool["text"].str.contains(r"[\r\n]")].copy()
    pool["norm"] = pool["text"].map(normalize)
    pool = pool.drop_duplicates("norm")
    pool = pool[
        ~pool["norm"].isin(set(test["norm"])) & ~pool["barcode"].str.lstrip("0").isin(set(test["code"].str.lstrip("0")))
    ]
    pool["label"] = pool["text"].map(weak_label)
    pool = pool.dropna(subset=["label"])
    sampled = pd.concat([group.sample(min(len(group), 60_000), random_state=42) for _, group in pool.groupby("label")])
    train = pd.concat([sampled[["norm", "label"]], fit[["norm", "label"]]], ignore_index=True).sample(
        frac=1, random_state=42
    )
    # Eliminate duplicate contradictory training labels; no holdout names enter fitting.
    counts = train.groupby("norm")["label"].nunique()
    train = train[train["norm"].isin(counts[counts == 1].index)].drop_duplicates("norm")
    assert not set(train["norm"]) & set(test["norm"])
    started = time.perf_counter()
    model = PerfumeTypeModel().fit(train["norm"].tolist(), train["label"].tolist())
    training_seconds = time.perf_counter() - started
    names = test["name"].tolist()
    predictions = model.clf.classes_[model.predict_proba(names).argmax(axis=1)]
    path = model.export(args.artifacts_dir, names[:1000])
    predictor = PerfumeTypePredictor(args.artifacts_dir)
    predictor.predict(names[0])
    started = time.perf_counter()
    for name in names[:1000]:
        predictor.predict(name)
    report = {
        "seed": 42,
        "test_size": 0.3,
        "split": "GroupShuffleSplit by normalized name; CSV holdout name and barcode exclusion",
        "training_rows": len(train),
        "test_rows": len(test),
        "classes": model.clf.classes_.tolist(),
        "training_seconds": training_seconds,
        "weights_bytes": path.stat().st_size,
        "runtime_1000_seconds": time.perf_counter() - started,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "accuracy_against_declared_type": float(accuracy_score(test["label"], predictions)),
        "macro_f1_against_declared_type": float(f1_score(test["label"], predictions, average="macro", zero_division=0)),
        "limits": (
            "Weak labels use current algorithms rules, not the old prototype fuzzy rules; "
            "declared labels are not expert ground truth. Metrics are classification, not mismatch-detection quality."
        ),
    }
    path.with_name("training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
