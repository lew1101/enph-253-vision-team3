from pathlib import Path

from grpc_tools import protoc


def main() -> None:
    vision_dir = Path(__file__).resolve().parents[1]
    proto_dir = vision_dir.parent / "lib" / "comms" / "proto"
    proto_file = proto_dir / "vision.proto"

    result = protoc.main(
        [
            "protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={vision_dir}",
            str(proto_file),
        ]
    )
    if result != 0:
        raise SystemExit(result)

    print(f"Generated {vision_dir / 'vision_pb2.py'}")
