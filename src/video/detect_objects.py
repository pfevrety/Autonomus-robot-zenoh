"""YOLO-based object detector running on the laptop side.

Subscribes to every camera's JPEG stream under ``demo/obj-detect/cams/*``,
runs Ultralytics YOLO on each frame, smooths the per-object confidence
with a median filter and the per-object centre with a quadratic-weighted
average, then re-publishes one message per detection on
``demo/obj-detect/objects/<cam>/<idx>``.

The ``Forwarder`` (``forwarder.py``) listens on ``**/objects/**`` and
filters out detections whose ``name`` is not in the user's target list.
"""

import json
import sys
import time
from collections import deque
from statistics import median

import cv2
import numpy as np
from ultralytics import YOLO

from common.zenoh_args import parse_zenoh_args

DEFAULT_PREFIX = "demo/obj-detect"
CONFIDENCE_HISTORY = 10
CENTER_HISTORY = 10
CAMERA_TIMEOUT_S = 2.0


def smooth_confidence(history: dict, name: str, confidence: float) -> float:
    history.setdefault(name, deque(maxlen=CONFIDENCE_HISTORY))
    history[name].append(confidence)
    return median(history[name])


def smooth_center(history: dict, name: str, center, confidence: float):
    history.setdefault(name, deque(maxlen=CENTER_HISTORY))
    history[name].append((center[0], center[1], confidence))
    points = list(history[name])

    weighted_x = weighted_y = total_weight = 0
    for i, (x, y, conf) in enumerate(points):
        # Quadratic time-weight so the most recent detections dominate the average.
        weight = ((i + 1) ** 2) * conf
        weighted_x += x * weight
        weighted_y += y * weight
        total_weight += weight

    if total_weight == 0:
        return center

    return [int(weighted_x / total_weight), int(weighted_y / total_weight)]


def main() -> int:
    parser = argparse_yolo_args()
    args, conf, _ = parse_zenoh_args(
        description="Banane v2.0 YOLO detector",
        default_prefix=DEFAULT_PREFIX,
        include_delay=False,
    )

    cams: dict = {}
    history_conf: dict = {}
    history_center: dict = {}
    model = YOLO(f"yolo26{args.model_size}.pt")

    def frames_listener(sample):
        cam = str(sample.key_expr).split("/")[-1]
        cams.setdefault(cam, {})
        cams[cam]["img"] = bytes(sample.payload)
        cams[cam]["img_time"] = time.time()

    print("[INFO] Opening Zenoh session...")
    zenoh.init_log_from_env_or("error")
    z = zenoh.open(conf)
    z.declare_subscriber(f"{args.prefix}/cams/*", frames_listener)

    try:
        while True:
            now = time.time()
            stale = [
                cam
                for cam, data in cams.items()
                if now - data.get("img_time", now) > CAMERA_TIMEOUT_S
            ]
            for cam in stale:
                del cams[cam]

            for cam in list(cams):
                npImage = np.frombuffer(cams[cam]["img"], dtype=np.uint8)
                matImage = cv2.imdecode(npImage, 1)
                if matImage is None:
                    continue

                height, width = matImage.shape[:2]
                results = model.predict(source=matImage, show_boxes=True, verbose=False)
                i = 0
                for result in results:
                    if result.boxes is None:
                        continue
                    for box in result.boxes:
                        for data in box.data:
                            data = data.tolist()
                            box_xyxy = [
                                [int(data[0]), int(data[1])],
                                [int(data[2]), int(data[1])],
                                [int(data[2]), int(data[3])],
                                [int(data[0]), int(data[3])],
                            ]
                            normalized_box = [
                                [data[0] / width, data[1] / height],
                                [data[2] / width, data[1] / height],
                                [data[2] / width, data[3] / height],
                                [data[0] / width, data[3] / height],
                            ]

                            confidence = float(data[4])
                            object_name = result.names[int(data[5])]

                            smoothed_confidence = smooth_confidence(
                                history_conf, object_name, confidence
                            )

                            center = [
                                int((data[0] + data[2]) / 2),
                                int((data[1] + data[3]) / 2),
                            ]
                            smoothed_center = smooth_center(
                                history_center,
                                object_name,
                                center,
                                smoothed_confidence,
                            )

                            z.put(
                                f"{args.prefix}/objects/{cam}/{i}",
                                json.dumps(
                                    {
                                        "name": object_name,
                                        "confiance": int(smoothed_confidence * 100),
                                        "box": box_xyxy,
                                        "normalized_box": normalized_box,
                                        "raw_center": center,
                                        "center": smoothed_center,
                                        "normalized_center": [
                                            smoothed_center[0] / width,
                                            smoothed_center[1] / height,
                                        ],
                                    }
                                ),
                            )
                            i += 1
    except KeyboardInterrupt:
        print("[INFO] Interrupted, shutting down...")
    finally:
        z.close()

    return 0


def argparse_yolo_args() -> "argparse.ArgumentParser":  # noqa: F821 - placeholder
    """Build the YOLO-specific argument parser.

    Imported lazily so the function reads top-down even though the
    ``argparse`` import is shared with the other CLI helpers below.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="detect_objects",
        description="Banane v2.0 YOLO detector",
    )
    parser.add_argument(
        "-s",
        "--model-size",
        type=str,
        default="s",
        help="YOLO model size: n, s, m, l, or x.",
    )
    return parser


if __name__ == "__main__":
    sys.exit(main())
