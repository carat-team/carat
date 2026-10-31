from carat_algorithms.core import CheckResult, CheckStatus, ProductCard, get_checks


def test_card_parses_api_field_names() -> None:
    card = ProductCard.model_validate(
        {"fullName": "Туалетная вода Example 50 мл", "tnVedCode10": "3303001000", "volume": {"value": 50, "unit": "мл"}}
    )

    assert card.full_name == "Туалетная вода Example 50 мл"
    assert card.tn_ved_code10 == "3303001000"
    assert card.volume is not None and card.volume.value == 50


def test_absent_fields_stay_none_and_empty_text_is_kept() -> None:
    card = ProductCard.model_validate({"brand": ""})

    assert card.brand == ""
    assert card.gtin is None
    assert card.photos == ()


def test_result_serializes_with_api_keys() -> None:
    result = CheckResult(
        check_id="volume_vs_name",
        status=CheckStatus.WARNING,
        reason_code="VOLUME_MISMATCH",
        explanation="Объём в названии 50 мл, в атрибуте 100 мл",
        field_refs=("fullName", "volume"),
        algorithm_version=1,
    )

    assert result.model_dump(mode="json") == {
        "check_id": "volume_vs_name",
        "status": "WARNING",
        "reason_code": "VOLUME_MISMATCH",
        "explanation": "Объём в названии 50 мл, в атрибуте 100 мл",
        "field_refs": ["fullName", "volume"],
        "algorithm_version": 1,
    }


def test_registered_check_ids_are_unique() -> None:
    check_ids = [check.check_id for check in get_checks()]

    assert len(check_ids) == len(set(check_ids))
