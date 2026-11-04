import pytest

from carat_algorithms.core import CheckResult, ProductCard, get_checks


def run_type(name: str | None, declared: str | None) -> CheckResult:
    check = next((item for item in get_checks() if item.check_id == "perfumery_type"), None)
    assert check is not None, "Perfumery type check must run through the shared registry"
    return check.run(ProductCard(full_name=name, perfumery_type=declared))


CASES: list[tuple[str | None, str | None, str]] = [
    ("Духи Rose 50 мл", "ДУХИ", "PASS"),
    ("Духи Rose 50 мл", "Парфюм", "PASS"),
    ("Духи Rose 50 мл", "parfum", "PASS"),
    ("Духи Rose 50 мл", "Парфюмированная вода", "WARNING"),
    ("Духи Rose 50 мл", "Парфюмерная вода", "WARNING"),
    ("Духи Rose 50 мл", "Eau de Parfum", "WARNING"),
    ("Духи Rose 50 мл", "EDP", "WARNING"),
    ("Духи Rose 50 мл", "Туалетная вода", "WARNING"),
    ("Духи Rose 50 мл", "EDT", "WARNING"),
    ("Духи Rose 50 мл", "Одеколон", "WARNING"),
    ("Парфюмированная вода Rose 50 мл", "ДУХИ", "WARNING"),
    ("Парфюмированная вода Rose 50 мл", "Парфюм", "WARNING"),
    ("Парфюмированная вода Rose 50 мл", "parfum", "WARNING"),
    ("Парфюмированная вода Rose 50 мл", "Парфюмированная вода", "PASS"),
    ("Парфюмированная вода Rose 50 мл", "Парфюмерная вода", "PASS"),
    ("Парфюмированная вода Rose 50 мл", "Eau de Parfum", "PASS"),
    ("Парфюмированная вода Rose 50 мл", "EDP", "PASS"),
    ("Парфюмированная вода Rose 50 мл", "Туалетная вода", "WARNING"),
    ("Парфюмированная вода Rose 50 мл", "EDT", "WARNING"),
    ("Парфюмированная вода Rose 50 мл", "Одеколон", "WARNING"),
    ("Парфюмерная вода Rose 50 мл", "ДУХИ", "WARNING"),
    ("Парфюмерная вода Rose 50 мл", "Парфюм", "WARNING"),
    ("Парфюмерная вода Rose 50 мл", "parfum", "WARNING"),
    ("Парфюмерная вода Rose 50 мл", "Парфюмированная вода", "PASS"),
    ("Парфюмерная вода Rose 50 мл", "Парфюмерная вода", "PASS"),
    ("Парфюмерная вода Rose 50 мл", "Eau de Parfum", "PASS"),
    ("Парфюмерная вода Rose 50 мл", "EDP", "PASS"),
    ("Парфюмерная вода Rose 50 мл", "Туалетная вода", "WARNING"),
    ("Парфюмерная вода Rose 50 мл", "EDT", "WARNING"),
    ("Парфюмерная вода Rose 50 мл", "Одеколон", "WARNING"),
    ("Туалетная вода Rose 50 мл", "ДУХИ", "WARNING"),
    ("Туалетная вода Rose 50 мл", "Парфюм", "WARNING"),
    ("Туалетная вода Rose 50 мл", "parfum", "WARNING"),
    ("Туалетная вода Rose 50 мл", "Парфюмированная вода", "WARNING"),
    ("Туалетная вода Rose 50 мл", "Парфюмерная вода", "WARNING"),
    ("Туалетная вода Rose 50 мл", "Eau de Parfum", "WARNING"),
    ("Туалетная вода Rose 50 мл", "EDP", "WARNING"),
    ("Туалетная вода Rose 50 мл", "Туалетная вода", "PASS"),
    ("Туалетная вода Rose 50 мл", "EDT", "PASS"),
    ("Туалетная вода Rose 50 мл", "Одеколон", "WARNING"),
    ("Одеколон Classic 100 мл", "ДУХИ", "WARNING"),
    ("Одеколон Classic 100 мл", "Парфюм", "WARNING"),
    ("Одеколон Classic 100 мл", "parfum", "WARNING"),
    ("Одеколон Classic 100 мл", "Парфюмированная вода", "WARNING"),
    ("Одеколон Classic 100 мл", "Парфюмерная вода", "WARNING"),
    ("Одеколон Classic 100 мл", "Eau de Parfum", "WARNING"),
    ("Одеколон Classic 100 мл", "EDP", "WARNING"),
    ("Одеколон Classic 100 мл", "Туалетная вода", "WARNING"),
    ("Одеколон Classic 100 мл", "EDT", "WARNING"),
    ("Одеколон Classic 100 мл", "Одеколон", "PASS"),
    ("Perfume mist Rose", "ДУХИ", "WARNING"),
    ("Perfume mist Rose", "Парфюм", "WARNING"),
    ("Perfume mist Rose", "parfum", "WARNING"),
    ("Perfume mist Rose", "Парфюмированная вода", "WARNING"),
    ("Perfume mist Rose", "Парфюмерная вода", "WARNING"),
    ("Perfume mist Rose", "Eau de Parfum", "WARNING"),
    ("Perfume mist Rose", "EDP", "WARNING"),
    ("Perfume mist Rose", "Туалетная вода", "WARNING"),
    ("Perfume mist Rose", "EDT", "WARNING"),
    ("Perfume mist Rose", "Одеколон", "WARNING"),
    ("Body mist Rose", "ДУХИ", "WARNING"),
    ("Body mist Rose", "Парфюм", "WARNING"),
    ("Body mist Rose", "parfum", "WARNING"),
    ("Body mist Rose", "Парфюмированная вода", "WARNING"),
    ("Body mist Rose", "Парфюмерная вода", "WARNING"),
    ("Body mist Rose", "Eau de Parfum", "WARNING"),
    ("Body mist Rose", "EDP", "WARNING"),
    ("Body mist Rose", "Туалетная вода", "WARNING"),
    ("Body mist Rose", "EDT", "WARNING"),
    ("Body mist Rose", "Одеколон", "WARNING"),
    ("Твердые духи Rose", "ДУХИ", "PASS"),
    ("Твердые духи Rose", "Парфюм", "PASS"),
    ("Твердые духи Rose", "parfum", "PASS"),
    ("Твердые духи Rose", "Парфюмированная вода", "WARNING"),
    ("Твердые духи Rose", "Парфюмерная вода", "WARNING"),
    ("Твердые духи Rose", "Eau de Parfum", "WARNING"),
    ("Твердые духи Rose", "EDP", "WARNING"),
    ("Твердые духи Rose", "Туалетная вода", "WARNING"),
    ("Твердые духи Rose", "EDT", "WARNING"),
    ("Твердые духи Rose", "Одеколон", "WARNING"),
    ("", "ДУХИ", "REVIEW"),
    (None, "ДУХИ", "NOT_CHECKED"),
    ("Духи Rose", "", "REVIEW"),
    ("Духи Rose", None, "NOT_CHECKED"),
    ("White Horse ALREHAB, 6 мл", "ДУХИ", "NOT_CHECKED"),
    ("  ДУХИ   Rose 50 мл  ", "духи", "PASS"),
    ("Eau de Parfum Rose 50 ml", "Парфюмерная вода", "PASS"),
    ("Туалетная вода Rose", "неизвестный тип", "REVIEW"),
    ("Твердые духи Rose", "твёрдые духи", "PASS"),
    ("Парфюмерная вода Rose", "Парфюмерная вода", "PASS"),
    ("Eau de parfum Rose", "Набор", "NOT_CHECKED"),
    ("Туалетная вода Rose", "EDT; ДУХИ", "REVIEW"),
    ("Туалетная вода Rose", "Духи/Одеколон", "REVIEW"),
    ("Туалетная вода и духи Rose", "ДУХИ", "PASS"),
    ("Туалетная вода и одеколон Rose", "Одеколон", "REVIEW"),
    ("Parfum de toilette Rose", "EDT", "PASS"),
    ("Твердые духи Rose", "Туалетная вода", "WARNING"),
    ("Парфюмерная вода Rose", "твёрдые духи", "WARNING"),
]


@pytest.mark.parametrize("name,declared,status", CASES)
def test_registered_perfumery_type(name: str | None, declared: str | None, status: str) -> None:
    result = run_type(name, declared)
    assert result.status == status
    assert result.reason_code
    assert result.explanation
    assert result.field_refs == ("fullName", "perfumeryType")
    assert result.algorithm_version == 2


@pytest.mark.parametrize(
    "name,declared,values",
    [
        ("Духи Rose", "ДУХИ", ("духи",)),
        ("Твердые духи Rose", "ДУХИ", ("твердые духи", "духи")),
        ("Туалетная вода и духи Rose", "ДУХИ", ("туалетная вода", "духи")),
        ("Туалетная вода и одеколон Rose", "Одеколон", ("туалетная вода", "одеколон")),
        ("Туалетная вода Rose", "неизвестный тип", ("туалетная вода", "неизвестный тип")),
        ("White Horse Rose", "ДУХИ", ("white horse rose", "духи")),
    ],
)
def test_explanation_includes_compared_values(name: str, declared: str, values: tuple[str, ...]) -> None:
    result = run_type(name, declared)
    assert all(value in result.explanation.lower() for value in values)
