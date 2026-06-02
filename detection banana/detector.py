import zenoh
import cv2
import numpy as np
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # downloads automatically on first run
BANANA_CLASS_ID = 46        # COCO class index for banana

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
        if cls_id == BANANA_CLASS_ID and conf > 0.4:
            banana_found = True
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(frame, f"Banana {conf:.0%}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    label = "🍌 BANANA DETECTED!" if banana_found else "No banana"
    color = (0, 200, 0) if banana_found else (80, 80, 80)
    cv2.putText(frame, label, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

    cv2.imshow("Banana Detector via Zenoh", frame)
    cv2.waitKey(1)

session = zenoh.open(zenoh.Config())
sub = session.declare_subscriber("cam/frame", on_frame)
print("Listening for frames on 'cam/frame'... (press Ctrl+C to stop)")

try:
    while True:
        pass
except KeyboardInterrupt:
    pass

sub.undeclare()
session.close()
cv2.destroyAllWindows()