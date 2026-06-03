import argparse
import json
import queue
import random
import threading
import time
import cv2
import imutils
import numpy as np
import zenoh

parser = argparse.ArgumentParser(
    prog="capture_video", description="zenoh object detection example video capture"
)
parser.add_argument("-m", "--mode", choices=["peer", "client"])
parser.add_argument("-e", "--connect", action="append")
parser.add_argument("-l", "--listen", action="append")
parser.add_argument("-i", "--id", type=int, default=random.randint(1, 999))
parser.add_argument(
    "-a", "--camera", default="default", choices=["default", "picamera"]
)
parser.add_argument("-w", "--width", type=int, default=1024)
parser.add_argument("-q", "--quality", type=int, default=80) 
parser.add_argument("-d", "--delay", type=float, default=0.02)
parser.add_argument("-p", "--prefix", default="demo/obj-detect")
parser.add_argument("-c", "--config")

args = parser.parse_args()

conf = (
    zenoh.Config.from_file(args.config) if args.config is not None else zenoh.Config()
)
if args.mode:
    conf.insert_json5("mode", json.dumps(args.mode))
if args.connect:
    conf.insert_json5("connect/endpoints", json.dumps(args.connect))
if args.listen:
    conf.insert_json5("listen/endpoints", json.dumps(args.listen))

jpeg_opts = [int(cv2.IMWRITE_JPEG_QUALITY), args.quality]
picamera = args.camera.startswith("picamera")
cam_id = args.id
resource_key = f"{args.prefix}/cams/{cam_id}"

print("[INFO] Open zenoh session...")
zenoh.init_log_from_env_or("error")
z = zenoh.open(conf)

frame_queue = queue.Queue(maxsize=2)
running = True


def processing_thread(zenoh_session, key, opts):
    while running:
        try:
            frame = frame_queue.get(timeout=1.0)
            if frame is None:
                continue

            success, jpeg = cv2.imencode(".jpg", frame, opts)
            if success:
                zenoh_session.put(key, jpeg.tobytes())

            frame_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[ERROR] Thread processing: {e}")


sender_thread = threading.Thread(
    target=processing_thread, args=(z, resource_key, jpeg_opts), daemon=True
)
sender_thread.start()

print(f"[INFO] Start video stream - Cam #{cam_id}")

if picamera:
    import picamera2
    from libcamera import Transform

    vs = picamera2.Picamera2()

    height = int(args.width * 0.75)
    config = vs.create_video_configuration(
        main={"size": (args.width, height), "format": "RGB888"},
        controls={"FrameRate": 90.0},
        transform=Transform(vflip=True),
    )
    config["buffer_count"] = 6
    vs.configure(config)
    vs.start()
else:
    from imutils.video import VideoStream

    vs = VideoStream(src=0).start()

time.sleep(1.0)

try:
    while True:
        if picamera:
            frame = vs.capture_array()
        else:
            raw = vs.read()
            if raw is None:
                continue
            frame = imutils.resize(raw, width=args.width)

        if not frame_queue.full():
            frame_queue.put_nowait(frame)
        else:
            pass

        time.sleep(args.delay)

except KeyboardInterrupt:
    print("[INFO] Interruption demandée...")

# Nettoyage propre
running = False
sender_thread.join(timeout=2.0)
vs.stop()
z.close()
print("[INFO] Stream stoppé.")