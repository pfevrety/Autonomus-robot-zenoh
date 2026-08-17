"""Minimal camera publisher for the standalone banana detector.

Reads frames from the default USB webcam and publishes them as JPEG on
the ``cam/frame`` Zenoh topic. Pairs with ``detector.py`` for a quick
two-script demo of the camera + Zenoh chain.
"""

import time

import cv2
import zenoh

PUBLISH_INTERVAL_S = 0.05


def main() -> int:
    session = zenoh.open(zenoh.Config())
    pub = session.declare_publisher("cam/frame")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open default camera")
        return 1

    print("[INFO] Publishing camera feed on 'cam/frame'")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            _, encoded = cv2.imencode(".jpg", frame)
            pub.put(encoded.tobytes())
            time.sleep(PUBLISH_INTERVAL_S)
    except KeyboardInterrupt:
        print("[INFO] Interrupted, shutting down...")
    finally:
        cap.release()
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
