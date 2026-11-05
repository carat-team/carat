"""Train and export the original word TF-IDF + SGD logistic classifier."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from carat_algorithms.text.perfumery_type.model import TOKEN_PATTERN, PerfumeTypePredictor, normalize
from numpy.typing import NDArray
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier


class PerfumeTypeModel:
    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.vec = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=2,
            token_pattern=TOKEN_PATTERN,
            max_features=300_000,
            sublinear_tf=True,
            dtype=np.float32,
        )
        self.clf = SGDClassifier(
            loss="log_loss",
            alpha=2e-6,
            class_weight="balanced",
            max_iter=30,
            random_state=seed,
            n_jobs=-1,
        )

    def fit(self, texts: Sequence[str], labels: Sequence[str]) -> PerfumeTypeModel:
        self.clf.fit(self.vec.fit_transform([normalize(text) for text in texts]), labels)
        return self

    def predict_proba(self, texts: Sequence[str]) -> NDArray[np.float64]:
        return self.clf.predict_proba(self.vec.transform([normalize(text) for text in texts]))

    def export(self, weights_dir: Path, validation_texts: Sequence[str]) -> Path:
        """Export data only; reject runtime drift before handing off the artifact."""
        if len(self.clf.classes_) < 3:
            raise ValueError("Export requires at least three classes (multiclass one-vs-rest)")
        directory = weights_dir / "perfume_type_classifier"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "model.json"
        payload: dict[str, Any] = {
            "format_version": 1,
            "preprocessing": "perfume_nfkc_v1",
            "seed": self.seed,
            "classes": self.clf.classes_.tolist(),
            "vocabulary": {term: int(index) for term, index in self.vec.vocabulary_.items()},
            "idf": self.vec.idf_.tolist(),
            "coefficients": self.clf.coef_.tolist(),
            "intercepts": self.clf.intercept_.tolist(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        runtime = PerfumeTypePredictor(weights_dir)
        expected = self.predict_proba(validation_texts)
        for text, row in zip(validation_texts, expected, strict=True):
            actual = runtime.predict(text)
            if not actual:  # Runtime abstains on names with no vocabulary features.
                continue
            np.testing.assert_allclose(
                [actual[label] for label in self.clf.classes_],
                row,
                rtol=1e-5,
                atol=1e-6,
            )
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix(".json.sha256").write_text(f"{checksum}  model.json\n", encoding="ascii")
        return path
