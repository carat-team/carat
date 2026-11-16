"""Cut out the main product from a photo."""

import io
import struct

import numpy as np
from PIL import Image, ImageOps

from carat_algorithms.vision.background.masks import Array, components, dilate, validate_mask
from carat_algorithms.vision.background.segmentation import Segmenter

MAX_CUTOUT_PIXELS = 24_000_000


class InvalidPhotoError(ValueError):
    """The photo cannot be decoded within the limits of the cutout operation."""


def cutout_photo(content: bytes, segmenter: Segmenter) -> bytes | None:
    """Return a transparent PNG at the photo's resolution, cropped to the product."""
    try:
        with Image.open(io.BytesIO(content), formats=["JPEG", "PNG", "WEBP"]) as source:
            if source.width * source.height > MAX_CUTOUT_PIXELS:
                raise InvalidPhotoError("Фото должно содержать не более 24 мегапикселей")
            with ImageOps.exif_transpose(source) as oriented:
                image = oriented.convert("RGBA")
    except InvalidPhotoError:
        raise
    except (
        OSError,
        SyntaxError,
        TypeError,
        ValueError,
        struct.error,
        ZeroDivisionError,
        Image.DecompressionBombError,
    ) as error:
        raise InvalidPhotoError("Не удалось открыть фото для вырезания фона") from error

    with Image.new("RGBA", image.size, "white") as white, Image.alpha_composite(white, image) as composite:
        model_input = composite.convert("RGB")
    with model_input:
        mask = segmenter.segment(model_input)
    validate_mask(mask, (image.height, image.width))
    visible_mask = np.minimum(mask, np.asarray(image.getchannel("A")))
    cropped = cutout_product(image, visible_mask)
    if cropped is None:
        return None
    output = io.BytesIO()
    cropped.save(output, format="PNG")
    return output.getvalue()


def cutout_product(image: Image.Image, mask: Array) -> Image.Image | None:
    validate_mask(mask, (image.height, image.width))
    labeling = components(mask)
    if not labeling.product_labels:
        return None
    product = labeling.product_region
    rows = np.flatnonzero(product.any(axis=1))
    columns = np.flatnonzero(product.any(axis=0))
    left, right = int(columns[0]), int(columns[-1]) + 1
    top, bottom = int(rows[0]), int(rows[-1]) + 1
    bounds = np.s_[top:bottom, left:right]
    alpha = np.where(dilate(product[bounds], 2), mask[bounds], np.uint8(0))
    cropped = image.crop((left, top, right, bottom)).convert("RGBA")
    cropped.putalpha(Image.fromarray(alpha))
    return cropped
