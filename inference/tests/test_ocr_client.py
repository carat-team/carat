import grpc
import sys
import os
from common import load_env_file

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'generated'))

from carat.inference import ocr_pb2
from carat.inference import ocr_pb2_grpc


def test_ocr(image_path: str) -> None:
    if not os.path.exists(image_path):
        print(f"ERROR: File not found: {image_path}")
        return

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print(f"Sending {len(image_bytes)} bytes to OCR...")

    target = f"{os.getenv('ML_GRPC_HOST', 'localhost')}:{os.getenv('ML_GRPC_PORT', '50051')}"
    channel = grpc.insecure_channel(target)
    stub = ocr_pb2_grpc.OcrStub(channel)

    try:
        response = stub.ReadText(
            ocr_pb2.OcrRequest(image_data=image_bytes),
            timeout=60.0
        )

        print("-" * 40)
        print(f"TEXT BLOCKS: {len(response.blocks)}")
        for block in response.blocks:
            print(f"  {block.text} ({block.confidence:.2f})")
        print("-" * 40)

    except grpc.RpcError as e:
        print(f"gRPC error: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ocr_client.py <path_to_image>")
        sys.exit(1)

    load_env_file(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    test_ocr(sys.argv[1])
