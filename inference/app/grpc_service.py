import logging
import os
import tempfile
import time
import threading

import grpc
from carat.inference import analyzer_pb2
from carat.inference import analyzer_pb2_grpc
from carat.inference import ocr_pb2
from carat.inference import ocr_pb2_grpc
from carat.inference import segmentation_pb2
from carat.inference import segmentation_pb2_grpc
from PIL import Image, UnidentifiedImageError

from app.detectors.ocr_detector import OcrDetector
from app.detectors.segmentation_detector import SegmentationDetector

_inference_lock = threading.Lock()


class AnalyzerServicer(analyzer_pb2_grpc.AnalyzerServicer):
    def __init__(self, photo_detector, video_detector, text_detector):
        self.photo_detector = photo_detector
        self.video_detector = video_detector
        self.text_detector = text_detector

    def AnalyzePhoto(self, request, context):
        image_bytes = request.image_data

        logging.info("=" * 60)
        logging.info("[Photo] New request received")
        logging.info("[Photo] Peer: %s", context.peer())
        logging.info(
            "[Photo] Data size: %s bytes (%.2f MB)",
            len(image_bytes),
            len(image_bytes) / 1024 / 1024,
        )

        if not image_bytes:
            logging.warning("[Photo] Empty request received, returning error")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Empty image bytes received")
            return analyzer_pb2.AnalyzeReply()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        logging.info("[Photo] Saved to temp file: %s", tmp_path)

        start_time = time.time()

        try:
            with _inference_lock:
                confidence, pred = self.photo_detector.predict_picture(tmp_path)
            return _reply_from_prediction("Photo", start_time, confidence, pred)
        except Exception as e:
            _set_internal_error(context, "Photo", start_time, e)
            return analyzer_pb2.AnalyzeReply()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logging.info("[Photo] Temp file deleted: %s", tmp_path)

    def AnalyzeVideo(self, request, context):
        video_bytes = request.video_data

        logging.info("=" * 60)
        logging.info("[Video] New request received")
        logging.info("[Video] Peer: %s", context.peer())
        logging.info(
            "[Video] Data size: %s bytes (%.2f MB)",
            len(video_bytes),
            len(video_bytes) / 1024 / 1024,
        )

        if not video_bytes:
            logging.warning("[Video] Empty request received, returning error")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Empty video bytes received")
            return analyzer_pb2.AnalyzeReply()

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_file.write(video_bytes)
            tmp_path = tmp_file.name
        logging.info("[Video] Saved to temp file: %s", tmp_path)

        start_time = time.time()

        try:
            with _inference_lock:
                confidence, pred = self.video_detector.predict_video(tmp_path)
            return _reply_from_prediction("Video", start_time, confidence, pred)
        except Exception as e:
            _set_internal_error(context, "Video", start_time, e)
            return analyzer_pb2.AnalyzeReply()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logging.info("[Video] Temp file deleted: %s", tmp_path)

    def AnalyzeText(self, request, context):
        text = request.text

        logging.info("=" * 60)
        logging.info("[Text] New request received")
        logging.info("[Text] Peer: %s", context.peer())
        logging.info("[Text] Text length: %s chars", len(text))
        logging.info("[Text] Content: %s...", text[:200])

        if not text:
            logging.warning("[Text] Empty request received, returning error")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Empty text received")
            return analyzer_pb2.AnalyzeReply()

        start_time = time.time()

        try:
            with _inference_lock:
                confidence, pred = self.text_detector.predict_text(text)
            return _reply_from_prediction("Text", start_time, confidence, pred)
        except Exception as e:
            _set_internal_error(context, "Text", start_time, e)
            return analyzer_pb2.AnalyzeReply()



class OcrServicer(ocr_pb2_grpc.OcrServicer):
    def __init__(self, ocr_detector: OcrDetector) -> None:
        self.ocr_detector = ocr_detector

    def ReadText(
        self, request: ocr_pb2.OcrRequest, context: grpc.ServicerContext
    ) -> ocr_pb2.OcrReply:
        image_bytes = request.image_data

        logging.info("=" * 60)
        logging.info("[OCR] New request received")
        logging.info("[OCR] Peer: %s", context.peer())
        logging.info("[OCR] Data size: %s bytes", len(image_bytes))

        if not image_bytes:
            logging.warning("[OCR] Empty request received, returning error")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Empty image bytes received")
            return ocr_pb2.OcrReply()

        start_time = time.time()

        try:
            with _inference_lock:
                blocks = self.ocr_detector.read_text(image_bytes)
        except (UnidentifiedImageError, Image.DecompressionBombError) as e:
            logging.warning("[OCR] Cannot decode image: %s", e)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Data is not a supported image")
            return ocr_pb2.OcrReply()
        except Exception as e:
            _set_internal_error(context, "OCR", start_time, e)
            return ocr_pb2.OcrReply()

        # Recognized text is product data, so only the block count is logged
        logging.info(
            "[OCR] Completed in %.3fs, %s text block(s)", time.time() - start_time, len(blocks)
        )
        return ocr_pb2.OcrReply(
            blocks=[ocr_pb2.TextBlock(text=text, confidence=confidence) for text, confidence in blocks]
        )

class SegmentationServicer(segmentation_pb2_grpc.SegmentationServicer):
    def __init__(self, segmentation_detector: SegmentationDetector) -> None:
        self.segmentation_detector = segmentation_detector

    def SegmentProduct(
        self, request: segmentation_pb2.SegmentationRequest, context: grpc.ServicerContext
    ) -> segmentation_pb2.SegmentationReply:
        image_bytes = request.image_data

        logging.info("=" * 60)
        logging.info("[Segmentation] New request received")
        logging.info("[Segmentation] Peer: %s", context.peer())
        logging.info("[Segmentation] Data size: %s bytes", len(image_bytes))

        if not image_bytes:
            logging.warning("[Segmentation] Empty request received, returning error")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Empty image bytes received")
            return segmentation_pb2.SegmentationReply()

        start_time = time.time()

        try:
            with _inference_lock:
                mask_png, width, height = self.segmentation_detector.segment(image_bytes)
        except (UnidentifiedImageError, Image.DecompressionBombError) as e:
            logging.warning("[Segmentation] Cannot decode image: %s", e)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Data is not a supported image")
            return segmentation_pb2.SegmentationReply()
        except Exception as e:
            _set_internal_error(context, "Segmentation", start_time, e)
            return segmentation_pb2.SegmentationReply()

        logging.info(
            "[Segmentation] Completed in %.3fs, mask %sx%s", time.time() - start_time, width, height
        )
        return segmentation_pb2.SegmentationReply(mask_png=mask_png, width=width, height=height)


def _reply_from_prediction(operation, start_time, confidence, pred):
    predicted_class = "human" if pred == 0 else "ai"
    elapsed = time.time() - start_time

    logging.info("[%s] Inference completed in %.3fs", operation, elapsed)
    logging.info(
        "[%s] Result: class=%s, confidence=%.4f",
        operation,
        predicted_class,
        confidence,
    )

    reply = analyzer_pb2.AnalyzeReply()
    setattr(reply, "class", predicted_class)
    reply.confidence = float(confidence)
    return reply


def _set_internal_error(context, operation, start_time, error):
    elapsed = time.time() - start_time
    error_msg = f"{operation} inference failed after {elapsed:.3f}s: {str(error)}"
    logging.error("[%s] %s", operation, error_msg)
    context.set_code(grpc.StatusCode.INTERNAL)
    context.set_details(error_msg)