from math import inf, nan

import pytest

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard, get_checks
from carat_algorithms.text.brand_value import BrandValueCheck, BrandValueConfig, ForbiddenBrandValue
from carat_algorithms.text.brand_value.matching import jaro_winkler_distance
from carat_algorithms.text.brand_value.normalization import normalize_brand_value
from carat_algorithms.text.brand_value.proposed import (
    PROPOSED_BRAND_STOP_PHRASES_V1,
    PROPOSED_LIST_STATUS,
    build_proposed_brand_value_config_v1,
)


def configured_check(*rules: ForbiddenBrandValue) -> BrandValueCheck:
    return BrandValueCheck(BrandValueConfig(forbidden_values=rules))


@pytest.mark.parametrize(
    ("brand", "status", "reason_code"),
    [
        pytest.param(None, CheckStatus.NOT_CHECKED, "BRAND_VALUE_MISSING", id="missing"),
        pytest.param("", CheckStatus.WARNING, "BRAND_VALUE_EMPTY", id="empty"),
        pytest.param(" \t\n ", CheckStatus.WARNING, "BRAND_VALUE_EMPTY", id="whitespace"),
        pytest.param("Без товарного знака", CheckStatus.PASS, "BRAND_VALUE_CANONICAL", id="canonical"),
        pytest.param(
            "  БЕЗ\u00a0ТОВАРНОГО   ЗНАКА  ",
            CheckStatus.PASS,
            "BRAND_VALUE_CANONICAL",
            id="canonical_normalized",
        ),
        pytest.param("Chanel", CheckStatus.NOT_CHECKED, "BRAND_VALUE_CONFIG_MISSING", id="config_missing"),
    ],
)
def test_unconfigured_check(brand: str | None, status: CheckStatus, reason_code: str) -> None:
    result = BrandValueCheck().run(ProductCard(brand=brand))
    assert result.status == status
    assert result.reason_code == reason_code


def test_empty_config_is_not_an_approved_stop_list() -> None:
    result = BrandValueCheck(BrandValueConfig()).run(ProductCard(brand="Chanel"))
    assert result.status == CheckStatus.NOT_CHECKED
    assert result.reason_code == "BRAND_VALUE_CONFIG_MISSING"


@pytest.mark.parametrize("brand", ["", " \t\n "])
def test_empty_value_explanation_includes_recommendation(brand: str) -> None:
    result = BrandValueCheck().run(ProductCard(brand=brand))
    assert result.explanation == (
        'Значение бренда пустое. Если товар не индивидуализирован товарным знаком, укажите "Без товарного знака"'
    )


def test_exact_forbidden_value_includes_compared_values() -> None:
    result = configured_check(ForbiddenBrandValue("отсутствует")).run(ProductCard(brand="  ОТСУТСТВУЕТ "))
    assert result.status == CheckStatus.WARNING
    assert result.reason_code == "BRAND_VALUE_FORBIDDEN"
    assert "ОТСУТСТВУЕТ" in result.explanation
    assert "отсутствует" in result.explanation
    assert 'Если товар не индивидуализирован товарным знаком, укажите "Без товарного знака"' in result.explanation


def test_exact_match_takes_priority_over_a_closer_fuzzy_candidate() -> None:
    result = configured_check(
        ForbiddenBrandValue("нету", max_distance=1.0),
        ForbiddenBrandValue("нет"),
    ).run(ProductCard(brand="нет"))
    assert result.status == CheckStatus.WARNING
    assert result.reason_code == "BRAND_VALUE_FORBIDDEN"
    assert '"нет"' in result.explanation


def test_similar_value_includes_distance_and_threshold() -> None:
    result = configured_check(ForbiddenBrandValue("отсутствует", max_distance=0.07)).run(
        ProductCard(brand="отсутсвует")
    )
    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "BRAND_VALUE_SIMILAR"
    assert "отсутсвует" in result.explanation
    assert "отсутствует" in result.explanation
    distance = jaro_winkler_distance(
        normalize_brand_value("отсутсвует"),
        normalize_brand_value("отсутствует"),
    )
    assert f"расстояние {distance:.4f}" in result.explanation
    assert "0.0700" in result.explanation
    assert (
        'Проверьте значение; если товар не индивидуализирован товарным знаком, укажите "Без товарного знака"'
    ) in result.explanation


def test_distance_threshold_is_inclusive() -> None:
    brand = normalize_brand_value("отсутсвует")
    stop_value = normalize_brand_value("отсутствует")
    distance = jaro_winkler_distance(brand, stop_value)

    included = configured_check(ForbiddenBrandValue(stop_value, max_distance=distance)).run(ProductCard(brand=brand))
    excluded = configured_check(ForbiddenBrandValue(stop_value, max_distance=distance - 0.000001)).run(
        ProductCard(brand=brand)
    )

    assert included.reason_code == "BRAND_VALUE_SIMILAR"
    assert excluded.reason_code == "BRAND_VALUE_OK"


@pytest.mark.parametrize("brand", ["Нету", "не", "Монетка", "РАННЕТ"])
def test_short_stop_value_uses_exact_matching_without_a_threshold(brand: str) -> None:
    result = configured_check(ForbiddenBrandValue("нет")).run(ProductCard(brand=brand))
    assert result.status == CheckStatus.PASS
    assert result.reason_code == "BRAND_VALUE_OK"


def test_canonical_value_stays_allowed_even_if_misconfigured_as_forbidden() -> None:
    result = configured_check(ForbiddenBrandValue("без товарного знака", max_distance=1.0)).run(
        ProductCard(brand="Без товарного знака")
    )
    assert result.status == CheckStatus.PASS
    assert result.reason_code == "BRAND_VALUE_CANONICAL"


def test_equal_distances_choose_normalized_stop_value_deterministically() -> None:
    check = configured_check(
        ForbiddenBrandValue("abcy", max_distance=1.0),
        ForbiddenBrandValue("abcx", max_distance=1.0),
    )
    result = check.run(ProductCard(brand="abcz"))
    assert result.reason_code == "BRAND_VALUE_SIMILAR"
    assert '"abcx"' in result.explanation


def test_result_contract() -> None:
    result = BrandValueCheck().run(ProductCard(brand=None))
    assert isinstance(result, CheckResult)
    assert result.check_id == "brand_value"
    assert result.field_refs == ("brand",)
    assert result.algorithm_version == 1
    assert result.explanation


def test_check_is_registered_without_an_approved_stop_list() -> None:
    check = next((item for item in get_checks() if item.check_id == "brand_value"), None)
    assert check is not None
    result = check.run(ProductCard(brand="Chanel"))
    assert result.status == CheckStatus.NOT_CHECKED
    assert result.reason_code == "BRAND_VALUE_CONFIG_MISSING"


def test_registry_accepts_explicit_brand_value_config() -> None:
    config = BrandValueConfig(forbidden_values=(ForbiddenBrandValue("отсутствует"),))
    check = next((item for item in get_checks(brand_value_config=config) if item.check_id == "brand_value"), None)
    assert check is not None
    result = check.run(ProductCard(brand="отсутствует"))
    assert result.status == CheckStatus.WARNING
    assert result.reason_code == "BRAND_VALUE_FORBIDDEN"


def test_existing_registry_call_with_weights_argument_stays_compatible() -> None:
    assert get_checks(None)


@pytest.mark.parametrize(
    ("value", "max_distance"),
    [
        pytest.param(" ", None, id="empty_value"),
        pytest.param("нет", -0.01, id="negative_threshold"),
        pytest.param("нет", 1.01, id="threshold_above_one"),
        pytest.param("нет", nan, id="nan_threshold"),
        pytest.param("нет", inf, id="positive_infinity_threshold"),
        pytest.param("нет", -inf, id="negative_infinity_threshold"),
    ],
)
def test_invalid_rule_configuration_is_rejected(value: str, max_distance: float | None) -> None:
    with pytest.raises(ValueError):
        ForbiddenBrandValue(value, max_distance=max_distance)


def test_duplicate_normalized_rules_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        BrandValueConfig(
            forbidden_values=(ForbiddenBrandValue("нет"), ForbiddenBrandValue("  НЕТ ")),
        )


def test_proposed_list_is_explicit_and_not_the_registry_default() -> None:
    assert PROPOSED_LIST_STATUS == "proposed_for_review_not_approved"
    assert PROPOSED_BRAND_STOP_PHRASES_V1
    default_check = next(item for item in get_checks() if item.check_id == "brand_value")
    assert default_check.run(ProductCard(brand="отсутствует")).reason_code == "BRAND_VALUE_CONFIG_MISSING"


def test_proposed_list_metadata_matches_runtime_rules() -> None:
    for candidate in PROPOSED_BRAND_STOP_PHRASES_V1:
        if candidate.mode == "exact":
            assert candidate.max_distance is None
        else:
            assert candidate.max_distance is not None

    config = build_proposed_brand_value_config_v1()
    assert len(config.forbidden_values) == len(PROPOSED_BRAND_STOP_PHRASES_V1)
