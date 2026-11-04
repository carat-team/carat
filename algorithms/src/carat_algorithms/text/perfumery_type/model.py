"""Portable TF-IDF/SGD inference without pickle or research-package imports."""

from __future__ import annotations

import json
import math
import re
import threading
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Protocol, cast

WEIGHTS_SUBDIRECTORY = "perfume_type_classifier"
WEIGHTS_FILENAME = "model.json"
TOKEN_PATTERN = r"(?u)[\w/]+"
_LATIN_TO_CYRILLIC = str.maketrans(dict(zip("aeopcxykmthbu", "аеорсхукмтнви", strict=True)))


def normalize(text: str) -> str:
    """Match the original experiment's normalization, shared by training and serving."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("ё", "е").replace("ı", "i").replace("’", "'").replace("`", "'")
    text = re.sub(r"([а-я])\.([а-я])", r"\1. \2", text)
    tokens = [
        token.translate(_LATIN_TO_CYRILLIC) if re.search(r"[а-я]", token) and re.search(r"[a-z]", token) else token
        for token in text.split()
    ]
    text = re.sub(r'[\u00ab\u00bb"“”„()\[\]{}<>|_*#,;:!?]+', " ", " ".join(tokens))
    return re.sub(r"\s+", " ", text).strip()


class TypePredictor(Protocol):
    def predict(self, text: str) -> dict[str, float] | None: ...


class PerfumeTypePredictor:
    """Load immutable exported parameters once; missing weights are optional."""

    def __init__(self, weights_dir: Path | None) -> None:
        self._path = weights_dir / WEIGHTS_SUBDIRECTORY / WEIGHTS_FILENAME if weights_dir else None
        self._lock = threading.Lock()
        self._parameters: tuple[list[str], dict[str, int], list[float], list[list[float]], list[float]] | None = None

    def _load(self) -> bool:
        with self._lock:
            if self._parameters is not None:
                return True
            if self._path is None or not self._path.is_file():
                return False
            data = cast(dict[str, object], json.loads(self._path.read_text(encoding="utf-8")))
            if data.get("format_version") != 1 or data.get("preprocessing") != "perfume_nfkc_v1":
                raise ValueError("Unsupported perfume model format or preprocessing")
            classes = cast(list[str], data["classes"])
            vocabulary = cast(dict[str, int], data["vocabulary"])
            idf = cast(list[float], data["idf"])
            coefficients = cast(list[list[float]], data["coefficients"])
            intercepts = cast(list[float], data["intercepts"])
            if (
                len(classes) < 3
                or len(set(classes)) != len(classes)
                or set(vocabulary.values()) != set(range(len(idf)))
                or len(coefficients) != len(classes)
                or len(intercepts) != len(classes)
                or any(len(row) != len(idf) for row in coefficients)
                or not all(math.isfinite(value) for row in [idf, intercepts, *coefficients] for value in row)
            ):
                raise ValueError("Invalid perfume model dimensions or parameters")
            self._parameters = classes, vocabulary, idf, coefficients, intercepts
            return True

    def predict(self, text: str) -> dict[str, float] | None:
        if not self._load():
            return None
        assert self._parameters is not None
        classes, vocabulary, idf, coefficients, intercepts = self._parameters
        tokens = re.findall(TOKEN_PATTERN, normalize(text))
        counts = Counter(tokens + [f"{first} {second}" for first, second in zip(tokens, tokens[1:], strict=False)])
        vector = {
            vocabulary[term]: (1 + math.log(count)) * idf[vocabulary[term]]
            for term, count in counts.items()
            if term in vocabulary
        }
        norm = math.sqrt(sum(value * value for value in vector.values()))
        if not norm:
            return {}
        scores: list[float] = []
        for row, intercept in zip(coefficients, intercepts, strict=True):
            logit = intercept + sum(row[index] * value / norm for index, value in vector.items())
            # Stable sigmoid, matching SGDClassifier(loss="log_loss") one-vs-rest.
            scores.append(1 / (1 + math.exp(-logit)) if logit >= 0 else math.exp(logit) / (1 + math.exp(logit)))
        total = sum(scores)
        return dict(zip(classes, [score / total for score in scores], strict=True)) if total else {}
