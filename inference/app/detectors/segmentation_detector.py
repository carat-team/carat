import io

from PIL import Image, ImageOps
from rembg import new_session, remove


class SegmentationDetector:
    def __init__(self, model_name: str) -> None:
        self.session = new_session(model_name)

    def segment(self, image_bytes: bytes) -> tuple[bytes, int, int]:
        """Returns a grayscale PNG mask of the salient objects and its size."""
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
        mask = remove(image, session=self.session, only_mask=True)

        buffer = io.BytesIO()
        mask.convert("L").save(buffer, "PNG")
        return buffer.getvalue(), mask.width, mask.height
