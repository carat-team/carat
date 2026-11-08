"""Check the brand field against an explicitly configured forbidden-value list."""

from dataclasses import dataclass

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard
from carat_algorithms.text.brand_value.config import BrandValueConfig, ForbiddenBrandValue
from carat_algorithms.text.brand_value.matching import jaro_winkler_distance
from carat_algorithms.text.brand_value.normalization import normalize_brand_value

CANONICAL_NO_BRAND_VALUE = "Без товарного знака"
_NORMALIZED_CANONICAL_VALUE = normalize_brand_value(CANONICAL_NO_BRAND_VALUE)
_NO_TRADEMARK_RECOMMENDATION = 'Если товар не индивидуализирован товарным знаком, укажите "Без товарного знака"'


@dataclass(frozen=True)
class _SimilarMatch:
    rule: ForbiddenBrandValue
    normalized_rule: str
    distance: float
    threshold: float


class BrandValueCheck:
    """Validate a category-independent brand value using configured text rules."""

    check_id = "brand_value"
    algorithm_version = 1

    def __init__(self, config: BrandValueConfig | None = None) -> None:
        self._config = config

    def run(self, card: ProductCard) -> CheckResult:
        if card.brand is None:
            return self._result(CheckStatus.NOT_CHECKED, "BRAND_VALUE_MISSING", "Значение бренда отсутствует")

        normalized_brand = normalize_brand_value(card.brand)
        if not normalized_brand:
            return self._result(
                CheckStatus.WARNING,
                "BRAND_VALUE_EMPTY",
                f"Значение бренда пустое. {_NO_TRADEMARK_RECOMMENDATION}",
            )
        if normalized_brand == _NORMALIZED_CANONICAL_VALUE:
            return self._result(
                CheckStatus.PASS,
                "BRAND_VALUE_CANONICAL",
                f'Значение бренда "{card.brand}" соответствует допустимой канонической записи',
            )
        if self._config is None or not self._config.forbidden_values:
            return self._result(
                CheckStatus.NOT_CHECKED,
                "BRAND_VALUE_CONFIG_MISSING",
                "Рабочий список запрещённых значений бренда не настроен",
            )

        exact_rule = self._find_exact_rule(normalized_brand)
        if exact_rule is not None:
            return self._result(
                CheckStatus.WARNING,
                "BRAND_VALUE_FORBIDDEN",
                f'Значение бренда "{card.brand}" совпадает со стоп-фразой "{exact_rule.value}". '
                f"{_NO_TRADEMARK_RECOMMENDATION}",
            )

        similar_match = self._find_similar_rule(normalized_brand)
        if similar_match is not None:
            return self._result(
                CheckStatus.REVIEW,
                "BRAND_VALUE_SIMILAR",
                f'Значение бренда "{card.brand}" похоже на стоп-фразу "{similar_match.rule.value}": '
                f"расстояние {similar_match.distance:.4f}, порог {similar_match.threshold:.4f}. "
                f"Проверьте значение; если товар не индивидуализирован товарным знаком, "
                f'укажите "{CANONICAL_NO_BRAND_VALUE}"',
            )

        return self._result(
            CheckStatus.PASS,
            "BRAND_VALUE_OK",
            f'Значение бренда "{card.brand}" не совпало с настроенными стоп-фразами',
        )

    def _find_exact_rule(self, normalized_brand: str) -> ForbiddenBrandValue | None:
        if self._config is None:
            return None
        for rule in self._config.forbidden_values:
            if normalized_brand == normalize_brand_value(rule.value):
                return rule
        return None

    def _find_similar_rule(self, normalized_brand: str) -> _SimilarMatch | None:
        if self._config is None:
            return None
        matches: list[_SimilarMatch] = []
        for rule in self._config.forbidden_values:
            if rule.max_distance is None:
                continue
            normalized_rule = normalize_brand_value(rule.value)
            distance = jaro_winkler_distance(normalized_brand, normalized_rule)
            if distance <= rule.max_distance:
                matches.append(
                    _SimilarMatch(
                        rule=rule,
                        normalized_rule=normalized_rule,
                        distance=distance,
                        threshold=rule.max_distance,
                    )
                )
        if not matches:
            return None
        return min(matches, key=lambda match: (match.distance, match.normalized_rule))

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("brand",),
            algorithm_version=self.algorithm_version,
        )
