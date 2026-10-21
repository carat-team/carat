"""Background check service: cut out the main object and check what is left around it."""

import io
import os

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError
from pydantic import BaseModel
from rembg import new_session, remove

MODEL = os.getenv("MODEL", "isnet-general-use")
WORK_SIZE = 512             # analysis runs on a copy with this long side
PRODUCT_PART_SHARE = 0.1  # mask parts at least this big relative to the largest one are the product too (bottle + its box)
MIN_OBJECT_SHARE = 0.005    # smaller blobs are noise, not objects (share of image area)
NEAR_DELTA_E = 10           # pixel this close to the background model counts as "same colour"
FAR_DELTA_E = 25            # pixel this far from it may belong to a foreign object
CLEAN_UNIFORMITY = 0.95     # share of "same colour" pixels for a clean background
CLEAN_EDGE_DENSITY = 0.02   # share of edge pixels allowed on a clean background

ImageFile.LOAD_TRUNCATED_IMAGES = True
session = new_session(MODEL)
app = FastAPI(
    title="Background check",
    version="0.1.0",
    description="Вырезает главный объект с фото товара и проверяет фон: "
                "чистый, неоднородный или с посторонними предметами.",
)


class Box(BaseModel):
    bbox: list[int]          # x, y, width, height in source image pixels
    area_share: float        # share of image area


class Foreign(Box):
    source: str              # "mask": separate object found by segmentation, "background": blob on the background


class Background(BaseModel):
    color: str | None        # dominant colour, #rrggbb
    uniformity: float        # share of background pixels close to the dominant colour
    edge_density: float      # share of background pixels on edges (texture, details)


class Analysis(BaseModel):
    verdict: str             # clean | noisy | objects | no_object
    ok: bool                 # true only for clean
    width: int
    height: int
    main_object: Box | None
    background: Background
    foreign_objects: list[Foreign]


def read_image(data: bytes) -> Image.Image:
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    except UnidentifiedImageError:
        raise HTTPException(415, "File is not an image")
    if img.mode in ("RGBA", "LA", "P"):
        flat = Image.new("RGB", img.size, "white")
        flat.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        return flat
    return img.convert("RGB")


def segment(img: Image.Image) -> tuple[np.ndarray, np.ndarray, int, np.ndarray, np.ndarray]:
    """Returns soft mask (0..255), binary mask and its connected components; component 0 is the background."""
    soft = np.array(remove(img, session=session, only_mask=True))
    mask = soft > 127
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    return soft, mask, n, labels, stats


def product_parts(n: int, stats: np.ndarray) -> list[int]:
    """Components that form the product: the largest one plus parts comparable to it (e.g. its box)."""
    areas = stats[1:n, cv2.CC_STAT_AREA]
    return [i + 1 for i, a in enumerate(areas) if a >= PRODUCT_PART_SHARE * areas.max()]


def bounding(stats: np.ndarray, parts: list[int]) -> tuple[int, int, int, int, int]:
    x0 = min(stats[i, 0] for i in parts)
    y0 = min(stats[i, 1] for i in parts)
    x1 = max(stats[i, 0] + stats[i, 2] for i in parts)
    y1 = max(stats[i, 1] + stats[i, 3] for i in parts)
    return x0, y0, x1 - x0, y1 - y0, sum(stats[i, 4] for i in parts)


def to_box(x: int, y: int, w: int, h: int, area: int, total: int, scale: float = 1.0) -> dict:
    return {"bbox": [round(v * scale) for v in (x, y, w, h)], "area_share": round(area / total, 4)}


def background_model(lab: np.ndarray, background: np.ndarray) -> np.ndarray:
    """Smooth quadratic surface fitted to the background colour, so plain colour and soft gradients both fit it."""
    h, w = background.shape
    yy, xx = np.mgrid[0:h, 0:w] / max(h, w)
    features = np.stack([np.ones_like(xx), xx, yy, xx * xx, xx * yy, yy * yy], axis=-1)
    idx = np.flatnonzero(background)[:: max(1, int(background.sum()) // 20000)]
    coef, *_ = np.linalg.lstsq(features.reshape(-1, 6)[idx], lab.reshape(-1, 3)[idx], rcond=None)
    return features @ coef


def analyze_image(img: Image.Image) -> dict:
    width, height = img.size
    scale = max(width, height) / WORK_SIZE
    small = img.resize((round(width / scale), round(height / scale))) if scale > 1 else img
    scale = max(scale, 1.0)

    _, mask, n, labels, stats = segment(small)
    total = mask.size
    min_area = MIN_OBJECT_SHARE * total
    result = {"width": width, "height": height, "foreign_objects": []}

    if n < 2:
        result.update(verdict="no_object", ok=False, main_object=None,
                      background={"color": None, "uniformity": 0.0, "edge_density": 0.0})
        return result

    parts = product_parts(n, stats)
    result["main_object"] = to_box(*bounding(stats, parts), total, scale)
    for i in range(1, n):
        if i not in parts and stats[i, cv2.CC_STAT_AREA] >= min_area:
            result["foreign_objects"].append({**to_box(*stats[i], total, scale), "source": "mask"})

    # Background = everything outside the objects, with a margin so object edges and shadows do not count
    margin = max(3, round(0.02 * min(mask.shape)))
    background = ~cv2.dilate(mask.astype(np.uint8), np.ones((margin, margin), np.uint8)).astype(bool)
    if background.sum() < min_area:
        background = ~mask

    rgb = np.asarray(small)
    lab = cv2.cvtColor(rgb.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    model = background_model(lab, background)
    delta = np.linalg.norm(lab - model, axis=2)
    uniformity = float((delta[background] < NEAR_DELTA_E).mean())

    edges = cv2.Canny(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), 50, 150) > 0
    edge_density = float(edges[background].mean())

    # Blobs on the background that clearly differ from it are foreign objects,
    # unless they touch the product: those are shadows, reflections or product parts the mask missed
    near_product = cv2.dilate(np.isin(labels, parts).astype(np.uint8), np.ones((2 * margin + 1,) * 2, np.uint8))
    far = ((delta > FAR_DELTA_E) & background).astype(np.uint8)
    far = cv2.morphologyEx(far, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    bn, blabels, bstats, _ = cv2.connectedComponentsWithStats(far, connectivity=8)
    for i in range(1, bn):
        if bstats[i, cv2.CC_STAT_AREA] >= min_area and not near_product[blabels == i].any():
            result["foreign_objects"].append({**to_box(*bstats[i], total, scale), "source": "background"})

    color = np.median(model[background], axis=0)
    dominant = cv2.cvtColor(color.reshape(1, 1, 3).astype(np.float32), cv2.COLOR_LAB2RGB)[0, 0]
    result["background"] = {
        "color": "#" + "".join(f"{round(float(np.clip(c, 0, 1)) * 255):02x}" for c in dominant),
        "uniformity": round(uniformity, 4),
        "edge_density": round(edge_density, 4),
    }

    if result["foreign_objects"]:
        verdict = "objects"
    elif uniformity >= CLEAN_UNIFORMITY and edge_density <= CLEAN_EDGE_DENSITY:
        verdict = "clean"
    else:
        verdict = "noisy"
    result.update(verdict=verdict, ok=verdict == "clean")
    return result


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": MODEL}


@app.post("/analyze", response_model=Analysis)
def analyze(file: UploadFile = File(..., description="Фото товара: JPEG, PNG или WebP")) -> dict:
    """Находит главный объект и проверяет фон вокруг него."""
    return analyze_image(read_image(file.file.read()))


@app.post("/cutout", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
def cutout(file: UploadFile = File(..., description="Фото товара: JPEG, PNG или WebP")) -> Response:
    """Возвращает PNG с главным объектом на прозрачном фоне, обрезанный по его рамке."""
    img = read_image(file.file.read())
    soft, _, n, labels, stats = segment(img)
    if n < 2:
        raise HTTPException(422, "No object found")
    parts = product_parts(n, stats)
    x, y, w, h, _ = bounding(stats, parts)
    # Keep the soft edge of the product only; other objects are dropped
    region = cv2.dilate(np.isin(labels, parts).astype(np.uint8), np.ones((5, 5), np.uint8))
    rgba = np.dstack([np.asarray(img), soft * region])
    buf = io.BytesIO()
    Image.fromarray(rgba[y:y + h, x:x + w], "RGBA").save(buf, "PNG")
    return Response(buf.getvalue(), media_type="image/png")
