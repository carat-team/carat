from pathlib import Path

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard
from carat_algorithms.text.perfumery_type.model import PerfumeTypePredictor, TypePredictor
from carat_algorithms.text.perfumery_type.rules import check_perfumery_name, normalize_declared_type

_MODEL_TYPES = {
    "духи": "ДУХИ",
    "твердые духи": "ДУХИ",
    "парфюмированная вода": "ПАРФЮМЕРНАЯ ВОДА",
    "туалетная вода": "ТУАЛЕТНАЯ ВОДА",
    "одеколон": "ОДЕКОЛОН",
    "мист": "СПРЕЙ ДЛЯ ТЕЛА",
}


class PerfumeryTypeCheck:
    """Compare explicit perfume type markers with the declared type (R3)."""

    check_id = "perfumery_type"
    algorithm_version = 2

    def __init__(self, weights_dir: Path | None = None, *, predictor: TypePredictor | None = None) -> None:
        self._predictor = predictor if predictor is not None else PerfumeTypePredictor(weights_dir)

    def run(self, card: ProductCard) -> CheckResult:
        if card.full_name is None or card.perfumery_type is None:
            return self._result(
                CheckStatus.NOT_CHECKED, "PERFUMERY_MISSING_INPUT", "Не указаны наименование или тип парфюмерии"
            )
        if not card.full_name.strip():
            return self._result(CheckStatus.REVIEW, "PERFUMERY_NAME_EMPTY", "Наименование товара пустое")
        if not card.perfumery_type.strip():
            return self._result(CheckStatus.REVIEW, "PERFUMERY_TYPE_EMPTY", "Тип парфюмерии пустой")
        finding = check_perfumery_name(card.full_name, card.perfumery_type)
        if finding["rule"] == "PERFUMERY_TYPE_NOT_FOUND":
            return self._model_result(card.full_name, card.perfumery_type)
        return self._result(finding["status"], finding["rule"], finding["message"])

    def _model_result(self, name: str, declared: str) -> CheckResult:
        canonical = normalize_declared_type(declared)
        model_type = _MODEL_TYPES.get(canonical or "")
        if declared.strip().upper().replace("Ё", "Е") == "ДУШИСТАЯ ВОДА":
            model_type = "ДУШИСТАЯ ВОДА"
        if model_type is None:
            return self._result(
                CheckStatus.REVIEW,
                "PERFUMERY_MODEL_UNSUPPORTED_TYPE",
                f"Тип атрибута '{declared}' не поддерживается моделью, в наименовании '{name}' нет маркера типа",
            )
        scores = self._predictor.predict(name)
        if scores is None:
            return self._result(
                CheckStatus.NOT_CHECKED,
                "PERFUMERY_MODEL_WEIGHTS_MISSING",
                f"В наименовании '{name}' нет маркера типа, заявлен '{declared}', модель не установлена",
            )
        if model_type not in scores:
            return self._result(
                CheckStatus.REVIEW,
                "PERFUMERY_MODEL_NO_EVIDENCE",
                f"Модель не может проверить тип '{declared}' по наименованию '{name}'",
            )
        predicted = max(scores, key=lambda label: scores[label])
        if scores[predicted] >= 0.9 and scores[model_type] < 0.1 and predicted != model_type:
            return self._result(
                CheckStatus.WARNING,
                "PERFUMERY_MODEL_MISMATCH",
                f"Модель предполагает тип '{predicted}' для наименования '{name}', в атрибуте указан '{declared}'",
            )
        # Weak labels do not establish that an unmarked name satisfies the requirement.
        return self._result(
            CheckStatus.REVIEW,
            "PERFUMERY_MODEL_REVIEW",
            f"В наименовании '{name}' нет явного типа, модель предполагает '{predicted}', заявлен '{declared}'",
        )

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("fullName", "perfumeryType"),
            algorithm_version=self.algorithm_version,
        )
