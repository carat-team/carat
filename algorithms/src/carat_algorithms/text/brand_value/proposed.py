"""Proposed brand stop phrases for review; this module is not enabled by default."""

from dataclasses import dataclass
from typing import Literal

from carat_algorithms.text.brand_value.config import BrandValueConfig, ForbiddenBrandValue

PROPOSED_LIST_VERSION = 1
PROPOSED_LIST_STATUS = "proposed_for_review_not_approved"

_AUTHOR_SOURCE = "Рабочая гипотеза автора задачи"
_XLSX_SOURCE = 'Выгрузка "Косметика и парфюмерия (все атрибуты).xlsx"'
_AUTHOR_AND_XLSX_SOURCE = f"{_AUTHOR_SOURCE}; {_XLSX_SOURCE}"


@dataclass(frozen=True)
class ProposedBrandStopPhrase:
    """One review candidate with provenance and an intentionally explicit matching mode."""

    value: str
    source: str
    mode: Literal["exact", "jaro_winkler"]
    max_distance: float | None = None

    def __post_init__(self) -> None:
        if self.mode == "exact" and self.max_distance is not None:
            raise ValueError("An exact proposed phrase must not have a distance threshold")
        if self.mode == "jaro_winkler" and self.max_distance is None:
            raise ValueError("A fuzzy proposed phrase must have a distance threshold")
        ForbiddenBrandValue(self.value, max_distance=self.max_distance)

    def to_rule(self) -> ForbiddenBrandValue:
        """Convert an explicitly selected proposal into runtime configuration."""

        return ForbiddenBrandValue(self.value, max_distance=self.max_distance)


PROPOSED_BRAND_STOP_PHRASES_V1: tuple[ProposedBrandStopPhrase, ...] = (
    ProposedBrandStopPhrase("отсутствует", _AUTHOR_AND_XLSX_SOURCE, "jaro_winkler", 0.07),
    ProposedBrandStopPhrase("нет товарного знака", _XLSX_SOURCE, "jaro_winkler", 0.06),
    ProposedBrandStopPhrase("без бренда", _AUTHOR_AND_XLSX_SOURCE, "jaro_winkler", 0.05),
    ProposedBrandStopPhrase("без торговой марки", _AUTHOR_AND_XLSX_SOURCE, "jaro_winkler", 0.05),
    ProposedBrandStopPhrase("без товарной марки", _XLSX_SOURCE, "jaro_winkler", 0.05),
    ProposedBrandStopPhrase("товарный знак отсутствует", _AUTHOR_AND_XLSX_SOURCE, "jaro_winkler", 0.06),
    ProposedBrandStopPhrase("нет", _AUTHOR_AND_XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("без знака", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("без тм", _AUTHOR_AND_XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("без тз", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("нет бренда", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("не указан", _AUTHOR_SOURCE, "exact"),
    ProposedBrandStopPhrase("не указано", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("без марки", _AUTHOR_SOURCE, "exact"),
    ProposedBrandStopPhrase("б/н", _AUTHOR_SOURCE, "exact"),
    ProposedBrandStopPhrase("no brand", _AUTHOR_AND_XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("no name", _AUTHOR_AND_XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("noname", _AUTHOR_AND_XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("честный знак", _AUTHOR_AND_XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("-", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("n/a", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("none", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("нет в справочнике", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("без названия бренда", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("без указания бренда", _XLSX_SOURCE, "exact"),
    ProposedBrandStopPhrase("товарного знака нет", _XLSX_SOURCE, "exact"),
)


def build_proposed_brand_value_config_v1() -> BrandValueConfig:
    """Build the unapproved V1 config only after an explicit caller decision."""

    return BrandValueConfig(forbidden_values=tuple(candidate.to_rule() for candidate in PROPOSED_BRAND_STOP_PHRASES_V1))
