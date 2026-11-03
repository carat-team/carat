import io
import struct
import zlib
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from carat_algorithms.core import CardPhoto, CheckStatus, ProductCard, get_checks


def scene(*rectangles: tuple[int, int, int, int]) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    image = np.full((200, 200, 3), 240, dtype=np.uint8)
    mask = np.zeros((200, 200), dtype=np.uint8)
    for x, y, width, height in rectangles:
        image[y : y + height, x : x + width] = 0
        mask[y : y + height, x : x + width] = 255
    return image, mask


def photo(image: np.ndarray[Any, Any]) -> CardPhoto:
    stream = io.BytesIO()
    Image.fromarray(image).save(stream, format="PNG")
    return CardPhoto(content=stream.getvalue())


def test_background_is_registered() -> None:
    check = next((item for item in get_checks() if item.check_id == "background"), None)
    assert check is not None, "Background check must run through the shared registry"
    assert check.run(ProductCard()).status == CheckStatus.NOT_CHECKED


def test_missing_weights_are_not_checked(tmp_path: Path) -> None:
    check = next(item for item in get_checks(tmp_path) if item.check_id == "background")
    image, _ = scene((70, 40, 60, 120))
    result = check.run(ProductCard(photos=(photo(image),)))
    assert result.status == CheckStatus.NOT_CHECKED
    assert result.reason_code == "BACKGROUND_WEIGHTS_MISSING"


def test_plain_background_is_clean() -> None:
    from carat_algorithms.vision.background.analysis import analyze_background

    image, mask = scene((70, 40, 60, 120))
    result = analyze_background(image, mask, scale=2)
    assert result.status == CheckStatus.PASS
    assert result.foreign_objects == ()
    assert result.main_box is not None
    assert result.main_box.x == 140 and result.main_box.height == 240
    assert result.background_color == "#f0f0f0"


def test_smooth_gradient_is_clean() -> None:
    from carat_algorithms.vision.background.analysis import analyze_background

    image, mask = scene((80, 50, 40, 100))
    values = 180 + np.arange(200) * 60 // 200
    for channel in range(3):
        image[:, :, channel] = values - channel * 20
    image[50:150, 80:120] = 0
    assert analyze_background(image, mask).status == CheckStatus.PASS


def test_textured_background_is_noisy() -> None:
    from carat_algorithms.vision.background.analysis import analyze_background

    image, mask = scene((80, 50, 40, 100))
    noise = np.random.default_rng(42).integers(120, 220, size=(200, 200), dtype=np.uint8)
    image[:] = noise[:, :, None]
    image[50:150, 80:120] = 0
    result = analyze_background(image, mask)
    assert result.status == CheckStatus.WARNING
    assert result.reason_code == "BACKGROUND_NOISY"


def test_separate_small_object_in_mask_is_foreign() -> None:
    from carat_algorithms.vision.background.analysis import analyze_background

    image, mask = scene((40, 40, 60, 120), (150, 150, 20, 20))
    image[150:170, 150:170] = (255, 0, 0)
    result = analyze_background(image, mask)
    assert result.reason_code == "BACKGROUND_FOREIGN_OBJECTS"
    assert len(result.foreign_objects) == 1
    assert result.foreign_objects[0].source == "mask"
    assert result.foreign_objects[0].box.x == 150


def test_bottle_and_box_are_one_product() -> None:
    from carat_algorithms.vision.background.analysis import analyze_background

    image, mask = scene((30, 40, 70, 120), (120, 80, 30, 80))
    result = analyze_background(image, mask)
    assert result.status == CheckStatus.PASS
    assert result.main_box is not None
    assert result.main_box.x == 30 and result.main_box.width == 120


def test_blob_missed_by_mask_is_foreign() -> None:
    from carat_algorithms.vision.background.analysis import analyze_background

    image, mask = scene((30, 40, 50, 120))
    image[20:50, 140:170] = (200, 30, 30)
    result = analyze_background(image, mask)
    assert result.status == CheckStatus.WARNING
    assert result.reason_code == "BACKGROUND_FOREIGN_OBJECTS"
    assert result.foreign_objects[0].source == "background"


def test_empty_mask_needs_review() -> None:
    from carat_algorithms.vision.background.analysis import analyze_background

    image, mask = scene()
    result = analyze_background(image, mask)
    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "BACKGROUND_NO_OBJECT"
    assert result.main_box is None


def test_full_frame_mask_has_no_background_to_assess() -> None:
    from carat_algorithms.vision.background.analysis import analyze_background

    image, mask = scene((0, 0, 200, 200))
    result = analyze_background(image, mask)
    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "BACKGROUND_AREA_TOO_SMALL"


class FixedMask:
    def __init__(self, mask: np.ndarray[Any, Any]) -> None:
        self.mask = mask

    def segment(self, image: Image.Image) -> np.ndarray[Any, Any]:
        return self.mask


def test_corrupt_photo_needs_review() -> None:
    from carat_algorithms.vision.background import BackgroundCheck

    _, mask = scene((70, 40, 60, 120))
    result = BackgroundCheck(segmenter=FixedMask(mask)).run(ProductCard(photos=(CardPhoto(content=b"invalid"),)))
    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "BACKGROUND_INVALID_PHOTO"


def test_mismatched_model_mask_needs_review() -> None:
    from carat_algorithms.vision.background import BackgroundCheck

    image, _ = scene((70, 40, 60, 120))
    result = BackgroundCheck(segmenter=FixedMask(np.zeros((5, 5), dtype=np.uint8))).run(
        ProductCard(photos=(photo(image),))
    )
    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "BACKGROUND_MASK_INVALID"


def test_check_uses_product_card_and_shared_result() -> None:
    from carat_algorithms.vision.background import BackgroundCheck

    image, mask = scene((70, 40, 60, 120))
    result = BackgroundCheck(segmenter=FixedMask(mask)).run(ProductCard(photos=(photo(image),)))
    assert result.status == CheckStatus.PASS
    assert result.field_refs == ("photos",) and result.algorithm_version == 1
    assert result.reason_code and result.explanation


def test_good_photo_does_not_hide_foreign_objects() -> None:
    from carat_algorithms.vision.background import BackgroundCheck

    good, mask = scene((30, 40, 50, 120))
    bad = good.copy()
    bad[20:50, 140:170] = (200, 30, 30)
    result = BackgroundCheck(segmenter=FixedMask(mask)).run(ProductCard(photos=(photo(good), photo(bad))))
    assert result.status == CheckStatus.WARNING


def test_cutout_keeps_product_and_soft_alpha() -> None:
    from carat_algorithms.vision.background.cutout import cutout_product

    image, mask = scene((40, 40, 60, 120), (150, 150, 20, 20))
    result = cutout_product(Image.fromarray(image), mask)
    assert result is not None
    assert result.mode == "RGBA" and result.size == (60, 120)
    assert np.asarray(result)[60, 30, 3] == 255


def test_cutout_of_empty_mask_is_absent() -> None:
    from carat_algorithms.vision.background.cutout import cutout_product

    image, mask = scene()
    assert cutout_product(Image.fromarray(image), mask) is None


def test_transparency_is_composited_on_white_and_large_photos_are_bounded() -> None:
    from carat_algorithms.vision.background import BackgroundCheck

    class InspectingSegmenter:
        def segment(self, image: Image.Image) -> np.ndarray[Any, Any]:
            assert image.mode == "RGB" and image.size == (512, 256)
            assert image.getpixel((0, 0)) == (255, 255, 255)
            return np.zeros((image.height, image.width), dtype=np.uint8)

    stream = io.BytesIO()
    Image.new("RGBA", (2048, 1024), (0, 0, 0, 0)).save(stream, format="PNG")
    result = BackgroundCheck(segmenter=InspectingSegmenter()).run(
        ProductCard(photos=(CardPhoto(content=stream.getvalue()),))
    )
    assert result.reason_code == "BACKGROUND_NO_OBJECT"


def test_clean_photo_does_not_hide_a_corrupt_photo() -> None:
    from carat_algorithms.vision.background import BackgroundCheck

    image, mask = scene((70, 40, 60, 120))
    result = BackgroundCheck(segmenter=FixedMask(mask)).run(
        ProductCard(photos=(photo(image), CardPhoto(content=b"invalid")))
    )
    assert result.status == CheckStatus.REVIEW


def test_exif_orientation_is_applied_before_segmentation() -> None:
    from carat_algorithms.vision.background import BackgroundCheck

    class InspectingSegmenter:
        def segment(self, image: Image.Image) -> np.ndarray[Any, Any]:
            assert image.size == (20, 40)
            return np.zeros((image.height, image.width), dtype=np.uint8)

    stream = io.BytesIO()
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (40, 20), "white").save(stream, format="JPEG", exif=exif)
    result = BackgroundCheck(segmenter=InspectingSegmenter()).run(
        ProductCard(photos=(CardPhoto(content=stream.getvalue()),))
    )
    assert result.reason_code == "BACKGROUND_NO_OBJECT"


def test_malformed_apng_needs_review_instead_of_crashing() -> None:
    from carat_algorithms.vision.background import BackgroundCheck

    image, mask = scene((70, 40, 60, 120))
    png = photo(image).content
    frame = b"fcTL" + struct.pack(">IIIIIHHBB", 42, 200, 200, 0, 0, 1, 10, 0, 0)
    invalid = png[:-12] + struct.pack(">I", len(frame) - 4) + frame + struct.pack(">I", zlib.crc32(frame)) + png[-12:]
    result = BackgroundCheck(segmenter=FixedMask(mask)).run(ProductCard(photos=(CardPhoto(content=invalid),)))
    assert result.status == CheckStatus.REVIEW
    assert result.reason_code == "BACKGROUND_INVALID_PHOTO"
