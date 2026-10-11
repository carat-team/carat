
import cv2
import numpy as np

from app.quality import QualityConfig, analyze_quality, verdict_for

RNG = np.random.default_rng(0)


def _textured(h=1080, w=1920):
    small = RNG.choice([50, 200], size=(h // 3 + 1, w // 3 + 1)).astype(np.uint8)
    img = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    return cv2.merge([img, img, img])


def test_sharp_vs_blurred():
    sharp = _textured()
    blurred = cv2.GaussianBlur(sharp, (0, 0), 15)
    assert analyze_quality(sharp).sharpness > analyze_quality(blurred).sharpness
    assert analyze_quality(blurred).sharpness < 30


def test_overexposed():
    img = np.full((1080, 1920, 3), 255, dtype=np.uint8)
    assert analyze_quality(img).overexposure == 0


def test_dark_frame():
    img = np.full((1080, 1920, 3), 8, dtype=np.uint8)
    assert analyze_quality(img).underexposure == 0


def test_resolution_curve():
    assert analyze_quality(_textured(1080, 1920)).resolution == 100
    assert analyze_quality(_textured(120, 160)).resolution == 50  # пол кривой
    assert 50 <= analyze_quality(_textured(500, 500)).resolution <= 65
    assert 61 <= analyze_quality(_textured(700, 700)).resolution <= 85
    assert 81 <= analyze_quality(_textured(1000, 1000)).resolution <= 100


def _product_on_white(obj, blur=0, size=1000):
    img = np.full((size, size, 3), 255, dtype=np.uint8)
    offset = (size - obj) // 2
    img[offset:offset + obj, offset:offset + obj] = _textured(obj, obj)
    if blur:
        img = cv2.GaussianBlur(img, (0, 0), blur)
    return img


def test_white_background_does_not_lower_sharpness():
    small = analyze_quality(_product_on_white(300)).sharpness
    large = analyze_quality(_product_on_white(700)).sharpness
    assert small >= 90 and large >= 90
    assert analyze_quality(_product_on_white(300, blur=4)).sharpness < 30


def test_white_background_is_not_overexposure():
    result = analyze_quality(_product_on_white(500))
    assert result.overexposure >= 90
    assert result.background_fraction > 0.5


def test_blown_out_object_is_penalized():
    img = _product_on_white(500)
    img[300:700, 300:700] = 255  # большой выбитый участок внутри товара
    assert analyze_quality(img).overexposure < 20


def test_good_image_is_ok():
    result = analyze_quality(_textured())
    assert result.verdict == "ok", result


def test_overall_is_min_and_weakest():
    img = np.full((1080, 1920, 3), 8, dtype=np.uint8)
    result = analyze_quality(img)
    assert result.overall == min(
        result.sharpness, result.overexposure,
        result.underexposure, result.resolution,
    )
    assert result.weakest == "underexposure"


def test_verdict_boundaries():
    cfg = QualityConfig()
    assert verdict_for(60, cfg) == "reject"
    assert verdict_for(61, cfg) == "review"
    assert verdict_for(80, cfg) == "review"
    assert verdict_for(81, cfg) == "ok"
