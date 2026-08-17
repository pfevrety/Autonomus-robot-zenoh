"""OpenCV debug viewer for camera frames and detected objects.

Subscribes to the ``demo/obj-detect`` namespace and opens one ``cv2``
window per camera, drawing the latest detection overlays on top of each
frame. Intended for development; the web UI uses ``web_display_video.py``
instead.
"""

import json
import sys
import time

import cv2
import numpy as np

from common.zenoh_args import parse_zenoh_args

DEFAULT_PREFIX = "demo/obj-detect"
DEFAULT_DELAY = 0.05
DETECTION_FRESHNESS_S = 0.2


def main() -> int:
    args, conf, _ = parse_zenoh_args(
        description="Banane v2.0 debug viewer",
        default_prefix=DEFAULT_PREFIX,
    )

    cams: dict = {}

    def frames_listener(sample):
        cam = str(sample.key_expr).split("/")[-1]
        cams.setdefault(cam, {})["img"] = bytes(sample.payload)

    def objects_listener(sample):
        chunks = str(sample.key_expr).split("/")
        cam, obj = chunks[-2], int(chunks[-1])
        cams.setdefault(cam, {}).setdefault("objects", {}).setdefault(obj, {})
        cams[cam]["objects"][obj] = json.loads(sample.payload.to_string())
        cams[cam]["objects"][obj]["time"] = time.time()

    print("[INFO] Opening Zenoh session...")
    zenoh.init_log_from_env_or("error")
    z = zenoh.open(conf)

    z.declare_subscriber(f"{args.prefix}/cams/*", frames_listener)
    z.declare_subscriber(f"{args.prefix}/objects/*/*", objects_listener)

    try:
        while True:
            now = time.time()
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
                        det["name"],
                        label_pos,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 0, 0),
                        2,
                    )
                    cv2.polylines(matImage, [box], True, (255, 0, 0), 2)
                cv2.imshow(f"Cam #{cam}", matImage)
            cv2.waitKey(1)
            time.sleep(args.delay)
    except KeyboardInterrupt:
        print("[INFO] Interrupted, shutting down...")
    finally:
        cv2.destroyAllWindows()
        z.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
