import logging
import time

import cv2
import grpc
import numpy as np
from carat.inference import image_quality_pb2
from carat.inference import image_quality_pb2_grpc

from app.quality.image_quality import analyze_quality


class QualityServicer(image_quality_pb2_grpc.ImageQualityServicer):
    def __init__(self, quality_config):
        self.quality_config = quality_config

    def Analyze(self, request, context):
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
            return image_quality_pb2.ImageQualityReply()

        start_time = time.time()

        try:
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                logging.warning("[Quality] Cannot decode image, returning error")
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Cannot decode image")
                return image_quality_pb2.ImageQualityReply()

            result = analyze_quality(image, self.quality_config)
        except Exception as e:
            _set_internal_error(context, start_time, e)
            return image_quality_pb2.ImageQualityReply()

        logging.info("[Quality] Analysis completed in %.3fs", time.time() - start_time)
        logging.info(
            "[Quality] Result: overall=%s, verdict=%s, weakest=%s",
            result.overall,
            result.verdict,
            result.weakest,
        )

        return image_quality_pb2.ImageQualityReply(
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


def _set_internal_error(context, start_time, error):
    elapsed = time.time() - start_time
    error_msg = f"Quality analysis failed after {elapsed:.3f}s: {str(error)}"
    logging.error("[Quality] %s", error_msg)
    context.set_code(grpc.StatusCode.INTERNAL)
    context.set_details(error_msg)
