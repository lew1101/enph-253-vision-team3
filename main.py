#!/usr/bin/env python3

from maix import app, camera, err, nn, pinmap, uart
import math

from vision_pb2 import (
    TELETUBBY_TYPE_GREEN,
    TELETUBBY_TYPE_PURPLE,
    TELETUBBY_TYPE_RED,
    TELETUBBY_TYPE_UNSPECIFIED,
    TELETUBBY_TYPE_YELLOW,
    TeletubbyDetection,
)
from uart import UartLink

MODEL_PATH = "/root/models/teletubby.mud"
LABEL_TO_TELETUBBY_TYPE = {
    "Red Teletubby": TELETUBBY_TYPE_RED,
    "Green Teletubby": TELETUBBY_TYPE_GREEN,
    "Yellow Teletubby": TELETUBBY_TYPE_YELLOW,
    "Purple Teletubby": TELETUBBY_TYPE_PURPLE,
}
CONFIDENCE_THRESHOLD = 0.50
IOU_THRESHOLD = 0.45

err.check_raise(
    pinmap.set_pin_function("A19", "UART1_TX"), "Failed to configure UART TX"
)

err.check_raise(
    pinmap.set_pin_function("A18", "UART1_RX"), "Failed to configure UART RX"
)

serial = uart.UART("/dev/ttyS1", 115200)


def clipped_box(detection, image_width, image_height):
    left = max(0, min(int(detection.x), image_width))
    top = max(0, min(int(detection.y), image_height))
    right = max(left, min(int(detection.x + detection.w), image_width))
    bottom = max(top, min(int(detection.y + detection.h), image_height))
    width = right - left
    height = bottom - top
    return None if width == 0 or height == 0 else (left, top, width, height)


def encode_detection(
    frame_sequence, image_width, image_height, detection, teletubby_type
):
    message = TeletubbyDetection(
        frame_sequence=frame_sequence,
        image_width=image_width,
        image_height=image_height,
        teletubby_type=teletubby_type,
    )

    box = (
        clipped_box(detection, image_width, image_height)
        if detection is not None
        else None
    )
    if box is not None:
        message.detected = True
        message.confidence = detection.score
        (
            message.bounding_box.x,
            message.bounding_box.y,
            message.bounding_box.width,
            message.bounding_box.height,
        ) = box

    return message.SerializeToString()


def target_class_types(detector):
    matching = {
        index: LABEL_TO_TELETUBBY_TYPE[label]
        for index, label in enumerate(detector.labels)
        if label in LABEL_TO_TELETUBBY_TYPE
    }
    if not matching:
        raise RuntimeError("YOLO model does not contain a recognized teletubby label")
    return matching


def best_teletubby(detections, class_types):
    matching = [
        item
        for item in detections
        if item.class_id in class_types
        and math.isfinite(item.score)
        and 0.0 <= item.score <= 1.0
    ]
    return max(matching, key=lambda item: item.score, default=None)


def main():
    detector = nn.YOLO11(MODEL_PATH, dual_buff=False)
    cam = camera.Camera(
        detector.input_width(), detector.input_height(), detector.input_format()
    )

    class_types = target_class_types(detector)
    link = UartLink(serial)
    frame_sequence = 1

    while not app.need_exit():
        image = cam.read()
        detections = detector.detect(
            image,
            conf_th=CONFIDENCE_THRESHOLD,
            iou_th=IOU_THRESHOLD,
        )
        detection = best_teletubby(detections, class_types)
        teletubby_type = (
            class_types[detection.class_id]
            if detection is not None
            else TELETUBBY_TYPE_UNSPECIFIED
        )

        payload = encode_detection(
            frame_sequence,
            cam.width(),
            cam.height(),
            detection,
            teletubby_type,
        )
        link.send(payload)
        frame_sequence = 1 if frame_sequence == 0xFFFFFFFF else frame_sequence + 1


if __name__ == "__main__":
    main()
