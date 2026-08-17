"""Single-class banana detector over Zenoh.

Subscribes to ``cam/frame`` JPEG frames and runs YOLOv8 on each one,
highlighting every banana (COCO class 46) above the 40 % confidence
threshold. Useful as a smoke test of the camera + Zenoh + YOLO chain
without having to run the full multi-class pipeline.
"""

import cv2
import numpy as np
import zenoh
from ultralytics import YOLO

BANANA_CLASS_ID = 46
CONFIDENCE_THRESHOLD = 0.4
BBOX_COLOR = (0, 255, 255)


def on_frame(sample):
    data = bytes(sample.payload)
    frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return

    results = model(frame, verbose=False)[0]

    banana_found = False
    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        if cls_id != BANANA_CLASS_ID or conf <= CONFIDENCE_THRESHOLD:
            continue
        banana_found = True
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(frame, (x1, y1), (x2, y2), BBOX_COLOR, 2)
        cv2.putText(
            frame,
            f"Banana {conf:.0%}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            BBOX_COLOR,
            2,
        )

    label = "BANANA DETECTED" if banana_found else "No banana"
    color = (0, 200, 0) if banana_found else (80, 80, 80)
    cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
    cv2.imshow("Banana Detector via Zenoh", frame)
    cv2.waitKey(1)


def main() -> int:
    global model
    model = YOLO("yolov8n.pt")
    session = zenoh.open(zenoh.Config())
    sub = session.declare_subscriber("cam/frame", on_frame)
    print("[INFO] Listening for frames on 'cam/frame' (Ctrl+C to stop)")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("[INFO] Interrupted, shutting down...")
    finally:
        sub.undeclare()
        session.close()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
