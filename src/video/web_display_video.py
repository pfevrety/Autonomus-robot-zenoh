"""MJPEG streaming generator for the web dashboard.

Subscribes to the same Zenoh topics as ``display_video.py`` but yields
multipart-encoded JPEG frames instead of opening OpenCV windows. The
FastAPI endpoint ``/video_feed`` consumes this generator.
"""

import json
import time

import cv2
import numpy as np
import zenoh

from common.zenoh_args import parse_zenoh_args

DEFAULT_PREFIX = "demo/obj-detect"
CAMERA_TIMEOUT_S = 2.0
DETECTION_FRESHNESS_S = 0.2
FRAME_LOOP_DELAY_S = 0.03


def main() -> int:
    """Entry point used when the file is run as a script for debugging.

    When ``main`` is imported by ``website/app.py``, only the
    ``stream_first_camera`` generator below is used; the rest of this
    function never executes.
    """
    args, conf, _ = parse_zenoh_args(
        description="Banane v2.0 web MJPEG streamer",
        default_prefix=DEFAULT_PREFIX,
        include_delay=False,
    )
    for chunk in stream_first_camera(args.prefix, conf):
        del chunk
        break
    return 0


def stream_first_camera(prefix: str, conf):
    """Yield one multipart JPEG frame per loop iteration.

    Iterates over every camera, drops stale ones, and streams the
    freshest frame for each camera in turn.
    """
    cams: dict = {}

    def frames_listener(sample):
        cam = str(sample.key_expr).split("/")[-1]
        cams.setdefault(cam, {})
        cams[cam]["img"] = bytes(sample.payload)
        cams[cam]["img_time"] = time.time()

    def objects_listener(sample):
        chunks = str(sample.key_expr).split("/")
        cam, obj = chunks[-2], int(chunks[-1])
        cams.setdefault(cam, {}).setdefault("objects", {}).setdefault(obj, {})
        cams[cam]["objects"][obj] = json.loads(sample.payload.to_string())
        cams[cam]["objects"][obj]["time"] = time.time()

    print("[INFO] Opening Zenoh session...")
    zenoh.init_log_from_env_or("error")
    z = zenoh.open(conf)

    z.declare_subscriber(f"{prefix}/cams/*", frames_listener)
    z.declare_subscriber(f"{prefix}/objects/*/*", objects_listener)

    while True:
        now = time.time()
        for cam in list(cams):
            if now - cams[cam].get("img_time", now) > CAMERA_TIMEOUT_S:
                del cams[cam]

        for cam in list(cams):
            if "img" not in cams[cam]:
                continue
            matImage = cv2.imdecode(
                np.frombuffer(cams[cam]["img"], dtype=np.uint8), 1
            )
            if matImage is None:
                continue

            for obj in cams[cam].get("objects", {}):
                det = cams[cam]["objects"][obj]
                if det["time"] <= now - DETECTION_FRESHNESS_S:
                    continue
                box = np.array(det["box"]).astype(int)
                label_pos = np.array(det["box"][0]).astype(int)
                cv2.putText(
                    matImage,
                    f"{det['name']}, {det['confiance']}%",
                    label_pos,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2,
                )
                cv2.polylines(matImage, [box], True, (255, 0, 0), 2)
                cv2.putText(
                    matImage,
                    str(np.array(det["normalized_center"])),
                    np.array(det["center"]).astype(int),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
                cv2.circle(
                    matImage,
                    np.array(det["center"]).astype(int),
                    5,
                    (0, 255, 0),
                    -1,
                )

            _, jpeg_buffer = cv2.imencode(".jpg", matImage)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg_buffer.tobytes()
                + b"\r\n"
            )

        time.sleep(FRAME_LOOP_DELAY_S)


if __name__ == "__main__":
    import sys

    sys.exit(main())
