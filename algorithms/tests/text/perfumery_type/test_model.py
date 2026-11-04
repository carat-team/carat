import json
import math
from pathlib import Path

import pytest

from carat_algorithms.core import CheckStatus, ProductCard, get_checks
from carat_algorithms.text.perfumery_type.check import PerfumeryTypeCheck
from carat_algorithms.text.perfumery_type.model import PerfumeTypePredictor, normalize


class StubPredictor:
    def __init__(self, scores: dict[str, float] | None) -> None:
        self.scores = scores
        self.calls = 0

    def predict(self, text: str) -> dict[str, float] | None:
        self.calls += 1
        return self.scores


@pytest.mark.parametrize(
    "scores,status",
    [
        (None, CheckStatus.NOT_CHECKED),
        ({}, CheckStatus.REVIEW),
        ({"ДУХИ": 0.05, "ТУАЛЕТНАЯ ВОДА": 0.95}, CheckStatus.WARNING),
        ({"ДУХИ": 0.1, "ТУАЛЕТНАЯ ВОДА": 0.9}, CheckStatus.REVIEW),
        ({"ДУХИ": 0.95, "ТУАЛЕТНАЯ ВОДА": 0.05}, CheckStatus.REVIEW),
        ({"ОДЕКОЛОН": 1.0}, CheckStatus.REVIEW),
    ],
)
def test_model_fallback(scores: dict[str, float] | None, status: CheckStatus) -> None:
    check = PerfumeryTypeCheck(predictor=StubPredictor(scores))
    result = check.run(ProductCard(full_name="Rose 50 мл", perfumery_type="ДУХИ"))
    assert result.status == status
    assert result.algorithm_version == 2
    assert result.field_refs == ("fullName", "perfumeryType")


@pytest.mark.parametrize(
    "name,declared",
    [(None, "ДУХИ"), ("", "ДУХИ"), ("Духи Rose", "EDT"), ("Rose", "Набор"), ("Rose", "неизвестно")],
)
def test_rules_and_preconditions_do_not_call_model(name: str | None, declared: str) -> None:
    predictor = StubPredictor({})
    PerfumeryTypeCheck(predictor=predictor).run(ProductCard(full_name=name, perfumery_type=declared))
    assert predictor.calls == 0


def write_weights(directory: Path) -> Path:
    family = directory / "perfume_type_classifier"
    family.mkdir()
    path = family / "model.json"
    path.write_text(
        json.dumps(
            {
                "format_version": 1,
                "preprocessing": "perfume_nfkc_v1",
                "classes": ["ДУХИ", "ТУАЛЕТНАЯ ВОДА", "ОДЕКОЛОН"],
                "vocabulary": {"rose": 0},
                "idf": [1.0],
                "coefficients": [[10.0], [-10.0], [-10.0]],
                "intercepts": [0.0, 0.0, 0.0],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_lazy_load_and_cache(tmp_path: Path) -> None:
    predictor = PerfumeTypePredictor(tmp_path)
    assert predictor.predict("rose") is None
    path = write_weights(tmp_path)
    scores = predictor.predict("ROSE")
    assert scores is not None
    assert scores["ДУХИ"] > 0.99
    assert math.isclose(sum(scores.values()), 1)
    path.unlink()
    assert predictor.predict("rose") == scores
    assert predictor.predict("unseen") == {}


def test_corrupt_weights_are_not_missing(tmp_path: Path) -> None:
    path = write_weights(tmp_path)
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        PerfumeTypePredictor(tmp_path).predict("rose")


def test_registry_passes_weights_directory(tmp_path: Path) -> None:
    write_weights(tmp_path)
    check = next(item for item in get_checks(tmp_path) if item.check_id == "perfumery_type")
    result = check.run(ProductCard(full_name="Rose", perfumery_type="ОДЕКОЛОН"))
    assert result.status == CheckStatus.WARNING
    assert result.reason_code == "PERFUMERY_MODEL_MISMATCH"


def test_normalization() -> None:
    assert normalize("  Туaл.вода (ROSE) Ё ı  ") == "туал. вода rose е i"
