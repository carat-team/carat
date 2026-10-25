import io

import easyocr
import numpy as np
from PIL import Image, ImageOps


class OcrDetector:
    def __init__(self, languages: list[str], min_confidence: float, max_image_side: int) -> None:
        self.reader = easyocr.Reader(languages, gpu=False, verbose=False)
        self.min_confidence = min_confidence
        self.max_image_side = max_image_side

    def read_text(self, image_bytes: bytes) -> list[tuple[str, float]]:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")

        # Large phone photos make OCR on CPU slow, so it runs on a downscaled copy
        scale = min(1.0, self.max_image_side / max(image.size))
        if scale < 1.0:
            image = image.resize((round(image.width * scale), round(image.height * scale)))

        return [
            (text, float(confidence))
            for _, text, confidence in self.reader.readtext(np.asarray(image))
            if confidence >= self.min_confidence
        ]
