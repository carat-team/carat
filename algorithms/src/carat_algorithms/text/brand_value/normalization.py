"""Normalization shared by the brand value matching rules."""

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_brand_value(value: str) -> str:
    """Normalize Unicode, case and whitespace without discarding punctuation."""

    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return _WHITESPACE_RE.sub(" ", normalized)
