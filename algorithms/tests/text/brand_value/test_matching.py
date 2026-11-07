import pytest

from carat_algorithms.text.brand_value.matching import jaro_winkler_distance


@pytest.mark.parametrize(
    ("left", "right", "expected_distance"),
    [
        pytest.param("MARTHA", "MARHTA", 0.0388888889, id="martha_transposition"),
        pytest.param("DIXON", "DICKSONX", 0.1866666667, id="dixon_insertion"),
        pytest.param("", "", 0.0, id="both_empty"),
        pytest.param("brand", "", 1.0, id="right_empty"),
        pytest.param("", "brand", 1.0, id="left_empty"),
    ],
)
def test_jaro_winkler_control_pairs(left: str, right: str, expected_distance: float) -> None:
    assert jaro_winkler_distance(left, right) == pytest.approx(expected_distance)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        pytest.param("brand", "brand", id="equal"),
        pytest.param("нет", "не", id="short_cyrillic"),
        pytest.param("Без товарного знака", "Без товара знака", id="long_cyrillic"),
        pytest.param("NoName", "Noeme", id="latin"),
    ],
)
def test_jaro_winkler_is_symmetric_and_bounded(left: str, right: str) -> None:
    distance = jaro_winkler_distance(left, right)
    assert 0.0 <= distance <= 1.0
    assert distance == pytest.approx(jaro_winkler_distance(right, left))
