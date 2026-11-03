"""Product-only RGBA crop; transport and storage of edited photos are separate tasks."""

import numpy as np
from PIL import Image

from carat_algorithms.vision.background.masks import Array, components, dilate, validate_mask


def cutout_product(image: Image.Image, mask: Array) -> Image.Image | None:
    validate_mask(mask, (image.height, image.width))
    labeling = components(mask)
    if not labeling.product_labels:
        return None
    product = labeling.product_region
    rows, columns = np.nonzero(product)
    alpha = np.where(dilate(product, 2), mask, 0).astype(np.uint8)
    rgba = np.dstack((np.asarray(image.convert("RGB")), alpha))
    return Image.fromarray(rgba).crop(
        (int(columns.min()), int(rows.min()), int(columns.max()) + 1, int(rows.max()) + 1)
    )
