import logging
import os
import tempfile
import time
import threading

import cv2
import grpc
import numpy as np
from carat.inference import analyzer_pb2
from carat.inference import analyzer_pb2_grpc

from app.quality import analyze_quality

_inference_lock = threading.Lock()


class AnalyzerServicer(analyzer_pb2_grpc.AnalyzerServicer):
    def __init__(self, photo_detector, video_detector, text_detector, quality_config):
        self.photo_detector = photo_detector
        self.video_detector = video_detector
        self.text_detector = text_detector
        self.quality_config = quality_config

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

    def AnalyzeQuality(self, request, context):
        image_bytes = request.image_data

        logging.info("=" * 60)
        logging.info("[Quality] New request received")
        logging.info("[Quality] Peer: %s", context.peer())
        logging.info(
            "[Quality] Data size: %s bytes (%.2f MB)",
            len(image_bytes),
            len(image_bytes) / 1024 / 1024,
        )

        if not image_bytes:
            logging.warning("[Quality] Empty request received, returning error")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Empty image bytes received")
            return analyzer_pb2.QualityReply()

        start_time = time.time()

        try:
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                logging.warning("[Quality] Cannot decode image, returning error")
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Cannot decode image")
                return analyzer_pb2.QualityReply()

            result = analyze_quality(image, self.quality_config)
        except Exception as e:
            _set_internal_error(context, "Quality", start_time, e)
            return analyzer_pb2.QualityReply()

        logging.info("[Quality] Analysis completed in %.3fs", time.time() - start_time)
        logging.info(
            "[Quality] Result: overall=%s, verdict=%s, weakest=%s",
            result.overall,
            result.verdict,
            result.weakest,
        )

        return analyzer_pb2.QualityReply(
            sharpness=result.sharpness,
            overexposure=result.overexposure,
            underexposure=result.underexposure,
            resolution=result.resolution,
            overall=result.overall,
            verdict=result.verdict,
            weakest=result.weakest,
            width=result.width,
            height=result.height,
        )


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