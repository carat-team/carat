import io
from collections.abc import Callable

import pytest


@pytest.fixture
def render_barcode() -> Callable[..., bytes]:
    """Render a barcode to PNG bytes, like BarcodeImages.java did for the Java tests."""
    import zxingcpp
    from PIL import Image

    def render(content: str, format_name: str, **options: object) -> bytes:
        code_format = getattr(zxingcpp.BarcodeFormat, format_name)
        # The stub leaves the writer options (e.g. gs1=True) untyped
        barcode = zxingcpp.create_barcode(content, code_format, **options)  # pyright: ignore[reportUnknownMemberType]
        image = zxingcpp.write_barcode_to_image(barcode, scale=4)
        height, width = int(image.shape[0]), int(image.shape[1])  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        buffer = io.BytesIO()
        Image.frombytes("L", (width, height), bytes(memoryview(image))).save(buffer, "PNG")
        return buffer.getvalue()

    return render


@pytest.fixture
def blank_png() -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (300, 200)).save(buffer, "PNG")
    return buffer.getvalue()
