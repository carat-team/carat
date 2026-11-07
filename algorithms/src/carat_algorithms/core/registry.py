"""Checks that run on every card. A check that is not listed here does not run."""

from pathlib import Path

from carat_algorithms.core.check import Check
from carat_algorithms.core.config import CheckConfig


def get_checks(weights_dir: Path | None = None, *, check_config: CheckConfig | None = None) -> list[Check]:
    """
    Returns a list of all checks that should be run on every card.
    Each check must be registered here to be run.
    """

    checks_config = check_config or CheckConfig()

    # Imported here: check modules import carat_algorithms.core, and core must stay import-light
    from carat_algorithms.identifiers.gtin import GtinFormatCheck
    from carat_algorithms.text.brand_value import BrandValueCheck
    from carat_algorithms.text.perfumery_type import PerfumeryTypeCheck
    from carat_algorithms.text.volume import VolumeVsNameCheck
    from carat_algorithms.vision.background import BackgroundCheck
    from carat_algorithms.vision.barcode import BarcodeOnPhotoCheck
    from carat_algorithms.vision.quality import ImageQualityCheck

    # Register checks here
    # The order of checks in this list is the order in which they will be run
    return [
        GtinFormatCheck(),
        BrandValueCheck(checks_config.brand_value_config),
        BarcodeOnPhotoCheck(),
        VolumeVsNameCheck(),
        ImageQualityCheck(),
        BackgroundCheck(weights_dir),
        PerfumeryTypeCheck(),
    ]
