import pytest

from carat_algorithms.core import CheckResult, CheckStatus, ProductCard, get_checks


def run_name_check(
    name: str | None,
    perfume_type: str | None,
) -> CheckResult:
    check = next(
        (item for item in get_checks() if item.check_id == "name_composition"),
        None,
    )
    assert check is not None, "Name composition check must be registered"

    return check.run(
        ProductCard(
            full_name=name,
            perfumery_type=perfume_type,
        )
    )


@pytest.mark.parametrize(
    "name,perfume_type,status,reason_code",
    [
        pytest.param(
            "Dior",
            "ДУХИ",
            CheckStatus.WARNING,
            "NAME_COMPOSITION_SINGLE_WORD",
            id="one_word",
        ),
        pytest.param(
            "Dior",
            None,
            CheckStatus.WARNING,
            "NAME_COMPOSITION_SINGLE_WORD",
            id="one_word_without_type",
        ),
        pytest.param(
            "Dior 50 мл",
            "ДУХИ",
            CheckStatus.PASS,
            "NAME_COMPOSITION_OK",
            id="brand_and_volume",
        ),
        pytest.param(
            "Dior50ml",
            "ДУХИ",
            CheckStatus.PASS,
            "NAME_COMPOSITION_OK",
            id="attached_volume",
        ),
        pytest.param(
            "Духи 50 мл",
            "ДУХИ",
            CheckStatus.WARNING,
            "NAME_COMPOSITION_ONLY_TYPE",
            id="type_and_volume",
        ),
        pytest.param(
            "Туалетная вода 100 мл",
            "ТУАЛЕТНАЯ ВОДА",
            CheckStatus.WARNING,
            "NAME_COMPOSITION_ONLY_TYPE",
            id="multiword_type_and_volume",
        ),
        pytest.param(
            "Парфюмерная вода 50 мл",
            "Eau de Parfum",
            CheckStatus.WARNING,
            "NAME_COMPOSITION_ONLY_TYPE",
            id="known_type_alias_and_volume",
        ),
        pytest.param(
            "Духи Chanel 50 мл",
            "ДУХИ",
            CheckStatus.PASS,
            "NAME_COMPOSITION_OK",
            id="type_brand_and_volume",
        ),
        pytest.param(
            "Dior Sauvage 100 мл",
            "ДУХИ",
            CheckStatus.PASS,
            "NAME_COMPOSITION_OK",
            id="brand_name_and_volume",
        ),
        pytest.param(
            "Особый аромат",
            "Особый аромат",
            CheckStatus.WARNING,
            "NAME_COMPOSITION_ONLY_TYPE",
            id="custom_type_exact",
        ),
        pytest.param(
            "Dior Sauvage",
            None,
            CheckStatus.NOT_CHECKED,
            "NAME_COMPOSITION_TYPE_MISSING",
            id="missing_type",
        ),
        pytest.param(
            "50 мл",
            "ДУХИ",
            CheckStatus.REVIEW,
            "NAME_COMPOSITION_VOLUME_ONLY",
            id="volume_only",
        ),
    ],
)
def test_registered_name_composition(
    name: str | None,
    perfume_type: str | None,
    status: CheckStatus,
    reason_code: str,
) -> None:
    result = run_name_check(name, perfume_type)

    assert result.status == status
    assert result.reason_code == reason_code
    assert result.explanation
    assert result.algorithm_version == 1


def test_missing_name() -> None:
    result = run_name_check(None, "ДУХИ")

    assert result.status == CheckStatus.NOT_CHECKED
    assert result.reason_code == "NAME_COMPOSITION_MISSING"


def test_empty_name() -> None:
    result = run_name_check("", "ДУХИ")

    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "NAME_COMPOSITION_EMPTY"
