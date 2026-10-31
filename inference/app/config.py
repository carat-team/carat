import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class GrpcSettings:
    host: str
    port: str
    max_message_mb: int


@dataclass(frozen=True)
class ImageModelSettings:
    general_weights: Path
    faces_weights: Path


@dataclass(frozen=True)
class TextModelSettings:
    model_weights: Path
    model_name: str


@dataclass(frozen=True)
class OcrModelSettings:
    languages: list[str]
    min_confidence: float
    max_image_side: int


@dataclass(frozen=True)
class SegmentationModelSettings:
    model_name: str


@dataclass(frozen=True)
class Settings:
    grpc: GrpcSettings
    image_model: ImageModelSettings
    text_model: TextModelSettings
    ocr_model: OcrModelSettings
    segmentation_model: SegmentationModelSettings


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _resolve_service_path(service_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return service_root / path


def load_settings(service_root: Path, project_root: Path) -> Settings:
    load_env_file(project_root / ".env")

    with (service_root / "config.yaml").open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    image_config = config["models"]["image"]
    text_config = config["models"]["text"]
    ocr_config = config["models"]["ocr"]
    segmentation_config = config["models"]["segmentation"]

    return Settings(
        grpc=GrpcSettings(
            host=os.getenv("GRPC_HOST", "[::]"),
            port=os.getenv("GRPC_PORT", "50051"),
            max_message_mb=int(config["app"].get("max_message_mb", 100)),
        ),
        image_model=ImageModelSettings(
            general_weights=_resolve_service_path(service_root, image_config["general_weights"]),
            faces_weights=_resolve_service_path(service_root, image_config["faces_weights"]),
        ),
        text_model=TextModelSettings(
            model_weights=_resolve_service_path(service_root, text_config["model_weights"]),
            model_name=text_config.get("model_name", "roberta-base"),
        ),
        ocr_model=OcrModelSettings(
            languages=list(ocr_config["languages"]),
            min_confidence=float(ocr_config.get("min_confidence", 0.3)),
            max_image_side=int(ocr_config.get("max_image_side", 1600)),
        ),
        segmentation_model=SegmentationModelSettings(
            model_name=segmentation_config.get("model_name", "isnet-general-use"),
        ),
    )