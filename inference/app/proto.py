import logging
import os
import subprocess
import sys
from pathlib import Path


def ensure_generated_proto(proto_dir: Path, generated_dir: Path) -> bool:
    proto_files = sorted((proto_dir / "carat" / "inference").glob("*.proto"))
    if not proto_files:
        logging.error("No proto files found in: %s", proto_dir / "carat" / "inference")
        return False

    generated_dir.mkdir(parents=True, exist_ok=True)

    if all(_is_up_to_date(proto_file, generated_dir) for proto_file in proto_files):
        logging.info("Proto files are up to date, skipping generation")
        return True

    logging.info("Generating gRPC files from proto...")
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"-I{proto_dir}",
                f"--python_out={generated_dir}",
                f"--grpc_python_out={generated_dir}",
                *(str(proto_file) for proto_file in proto_files),
            ],
            check=True,
        )
        logging.info("gRPC files generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error("Failed to generate gRPC files: %s", e)
        return False


def _is_up_to_date(proto_file: Path, generated_dir: Path) -> bool:
    pb2_file = generated_dir / "carat" / "inference" / f"{proto_file.stem}_pb2.py"
    pb2_grpc_file = generated_dir / "carat" / "inference" / f"{proto_file.stem}_pb2_grpc.py"
    if not (pb2_file.exists() and pb2_grpc_file.exists()):
        return False
    return os.path.getmtime(pb2_file) > os.path.getmtime(proto_file)
