"""Barcode decoding with zxing-cpp. Ported from BarcodeReader.java (PR #21, tag legacy/java-backend)."""

import io
from dataclasses import dataclass

from carat_algorithms.identifiers.gtin import CodeFormat


@dataclass(frozen=True)
class DecodedCode:
    text: str
    code_format: CodeFormat


def read_codes(image_bytes: bytes) -> list[DecodedCode] | None:
    """Decode every barcode on a photo. Returns None when the bytes are not a readable image."""
    # Heavy imports stay inside the function: the vision extra is optional
    import zxingcpp
    from PIL import Image, UnidentifiedImageError

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("L")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        return None

    formats = {
        zxingcpp.BarcodeFormat.EAN13: CodeFormat.EAN_13,
        zxingcpp.BarcodeFormat.EAN8: CodeFormat.EAN_8,
        zxingcpp.BarcodeFormat.UPCA: CodeFormat.UPC_A,
        zxingcpp.BarcodeFormat.UPCE: CodeFormat.UPC_E,
        zxingcpp.BarcodeFormat.ITF: CodeFormat.ITF,
        zxingcpp.BarcodeFormat.ITF14: CodeFormat.ITF,
        zxingcpp.BarcodeFormat.DataMatrix: CodeFormat.DATA_MATRIX,
    }
    codes: list[DecodedCode] = []
    # Plain text keeps the GS separator inside Chestny Znak codes, like ZXing Java did
    for barcode in zxingcpp.read_barcodes(image, text_mode=zxingcpp.TextMode.Plain):
        code_format = formats.get(barcode.format, CodeFormat.OTHER)
        text = barcode.text
        if code_format is CodeFormat.UPC_E:
            # zxing-cpp reports UPC-E expanded to 13 digits; the original 8 digits sit in `extra`
            extra = barcode.extra
            if isinstance(extra, dict) and isinstance(upce := extra.get("UPCE"), str):  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                text = upce
        codes.append(DecodedCode(text, code_format))
    return list(dict.fromkeys(codes))
