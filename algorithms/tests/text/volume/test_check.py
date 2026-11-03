import pytest

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard, get_checks


def run_volume(card: ProductCard) -> CheckResult:
    check = next((item for item in get_checks() if item.check_id == "volume_vs_name"), None)
    assert check is not None, "Volume check must run through the shared registry"
    return check.run(card)


@pytest.mark.parametrize(
    ("name", "volume", "status", "reason"),
    [
        ("Духи 50 мл", {"value": 100, "unit": "мл"}, CheckStatus.WARNING, "VOLUME_MISMATCH"),
        ("Духи 0,05 л", {"value": 50, "unit": "мл"}, CheckStatus.PASS, "VOLUME_MATCH"),
        ("Набор 2 x 5 мл + 10 мл", {"value": 20, "unit": "мл"}, CheckStatus.PASS, "VOLUME_SET_MATCH"),
        (None, {"value": 50, "unit": "мл"}, CheckStatus.NOT_CHECKED, "VOLUME_MISSING_INPUT"),
        ("Духи 50 мл", None, CheckStatus.NOT_CHECKED, "VOLUME_MISSING_INPUT"),
        ("", {"value": 50, "unit": "мл"}, CheckStatus.REVIEW, "VOLUME_NAME_EMPTY"),
        ("Духи 50 г", {"value": 50, "unit": "мл"}, CheckStatus.REVIEW, "VOLUME_DIMENSION"),
        ("Духи 50", {"value": 50, "unit": "мл"}, CheckStatus.REVIEW, "VOLUME_UNIT_MISSING"),
        ("Духи 50 мл", {"value": 50, "unit": ""}, CheckStatus.REVIEW, "VOLUME_UNIT_EMPTY"),
    ],
)
def test_registered_volume_check(
    name: str | None, volume: dict[str, object] | None, status: CheckStatus, reason: str
) -> None:
    result = run_volume(ProductCard.model_validate({"fullName": name, "volume": volume}))

    assert result.status == status
    assert result.reason_code == reason
    assert result.field_refs == ("fullName", "volume")
    assert result.algorithm_version == 1
    assert result.explanation


@pytest.mark.parametrize("count,total", [("25,5", 20), ("10,5", 10), ("100,5", 100)])
def test_fractional_suffix_count_is_never_truncated(count: str, total: int) -> None:
    result = run_volume(
        ProductCard.model_validate({"fullName": f"Набор 10 мл x {count}", "volume": {"value": total, "unit": "мл"}})
    )
    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "VOLUME_SET_AMBIGUOUS"
