import argparse
import imutils
import time
import cv2
import json
import random
import zenoh
import numpy as np

parser = argparse.ArgumentParser(
    prog="capture_video", description="zenoh object detection example video capture"
)
parser.add_argument(
    "-m", "--mode", type=str, choices=["peer", "client"], help="The zenoh session mode."
)
parser.add_argument(
    "-e",
    "--connect",
    type=str,
    metavar="ENDPOINT",
    action="append",
    help="zenoh endpoints to connect to.",
)
parser.add_argument(
    "-l",
    "--listen",
    type=str,
    metavar="ENDPOINT",
    action="append",
    help="zenoh endpoints to listen on.",
)
parser.add_argument(
    "-i", "--id", type=int, default=random.randint(1, 999), help="The Camera ID."
)
parser.add_argument(
    "-a",
    "--camera",
    type=str,
    default="default",
    choices=["default", "picamera"],
    help="The type of camera to use.",
)
parser.add_argument(
    "-w", "--width", type=int, default=1024, help="width of the published frames"
)
parser.add_argument(
    "-q",
    "--quality",
    type=int,
    default=95,
    help="quality of the published frames (0 - 100)",
)
parser.add_argument(
    "-d",
    "--delay",
    type=float,
    default=0.05,
    help="delay between each frame in seconds",
)
parser.add_argument(
    "-p", "--prefix", type=str, default="demo/obj-detect", help="resources prefix"
)
parser.add_argument(
    "-c", "--config", type=str, metavar="FILE", help="A zenoh configuration file."
)

args = parser.parse_args()
conf = (
    zenoh.Config.from_file(args.config) if args.config is not None else zenoh.Config()
)
if args.mode is not None:
    conf.insert_json5("mode", json.dumps(args.mode))
if args.connect is not None:
    conf.insert_json5("connect/endpoints", json.dumps(args.connect))
if args.listen is not None:
    conf.insert_json5("listen/endpoints", json.dumps(args.listen))

jpeg_opts = [int(cv2.IMWRITE_JPEG_QUALITY), args.quality]
picamera = args.camera.startswith("picamera")
cam_id = args.id

print("[INFO] Open zenoh session...")
zenoh.init_log_from_env_or("error")
z = zenoh.open(conf)

print("[INFO] Start video stream - Cam #{}".format(cam_id))
if picamera:
    import picamera2
    
    vs = picamera2.Picamera2()
    
    # 1. HARDWARE SELECTION: Force a high framerate (e.g., 90 or 120 FPS)
    # 2. HARDWARE TRANSFORMS: Let the camera sensor handle the vertical flip (vflip)
    config = vs.create_video_configuration(
        main={"size": (args.width, int(args.width * 0.75)), "format": "XRGB8888"},
        controls={"FrameRate": 90.0}, # Adjust based on your module (90 for v2, 120 for v3)
        transform=picamera2.Transform(vflip=True) 
    )
    
    # Boost buffer count to prevent frame drops if Zenoh network I/O lags slightly
    config["buffer_count"] = 6 
    
    vs.configure(config)
    vs.start()
else:
    from imutils.video import VideoStream
    vs = VideoStream(src=0).start()

time.sleep(1.0)

# Main Loop Optimized for Speed
while True:
    try:
        if picamera:
            # Captures array that is ALREADY flipped and correctly sized by hardware
            frame = vs.capture_array()
        else:
            raw = vs.read()
            frame = imutils.resize(raw, width=args.width)

        # Encode to JPEG
        _, jpeg = cv2.imencode(".jpg", frame, jpeg_opts)

        # Publish over Zenoh (Zenoh's put is asynchronous by default)
        z.put("{}/cams/{}".format(args.prefix, cam_id), jpeg.tobytes())
        
    except KeyboardInterrupt:
        break

# Cleanup
vs.stop()
z.close()