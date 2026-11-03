"""Checks that run on every card. A check that is not listed here does not run."""

from carat_algorithms.core.check import Check


def get_checks() -> list[Check]:
    """
    Returns a list of all checks that should be run on every card.
    Each check must be registered here to be run.
    """
    
    # Imported here: check modules import carat_algorithms.core, and core must stay import-light
    from carat_algorithms.identifiers.gtin import GtinFormatCheck
    from carat_algorithms.text.volume import VolumeVsNameCheck
    from carat_algorithms.vision.barcode import BarcodeOnPhotoCheck

    # Register checks here
    # The order of checks in this list is the order in which they will be run
    return [
        GtinFormatCheck(),
        BarcodeOnPhotoCheck(),
        VolumeVsNameCheck()
    ]
