import zenoh
import cv2
import time

session = zenoh.open(zenoh.Config())
pub = session.declare_publisher("cam/frame")

cap = cv2.VideoCapture(0)
print("Publishing camera feed on 'cam/frame'...")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    _, encoded = cv2.imencode(".jpg", frame)
    pub.put(encoded.tobytes())
    time.sleep(0.05)  # ~20 fps

cap.release()
session.close()