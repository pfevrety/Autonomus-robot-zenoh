"""Development mock publisher.

Pushes a synthetic detection on ``robot/aimed`` so the aim loop, webapp,
or any other subscriber can be exercised without a real camera or YOLO
detector running. Useful for end-to-end smoke tests on the laptop.
"""

import json
import time

import zenoh

PUBLISH_INTERVAL_S = 0.1
ITERATIONS = 30


def main() -> int:
    session = zenoh.open(zenoh.Config())
    try:
        for i in range(ITERATIONS):
            payload = json.dumps(
                {
                    "name": "banana",
                    "confiance": 99,
                    "box": [100, 150, 200, 250],
                    "normalized_box": [0.1, 0.15, 0.2, 0.25],
                    "raw_center": [150, 200],
                    "center": [150, 200],
                    "normalized_center": [
                        (100 + i) / 200,
                        200 / 250,
                    ],
                }
            )
            session.put("robot/aimed", payload)
            time.sleep(PUBLISH_INTERVAL_S)
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
