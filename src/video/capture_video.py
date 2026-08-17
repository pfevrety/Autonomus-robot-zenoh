"""Camera capture script for the Raspberry Pi.

Reads frames from either a Pi Camera (via ``picamera2``) or a USB webcam
(via ``imutils``), encodes each frame as JPEG, and publishes it on
``demo/obj-detect/cams/<id>``. Encoding and publishing happen on a
dedicated thread so the capture loop can keep grabbing at the requested
rate even when Zenoh is briefly slow.
"""

import argparse
import random
import sys
import threading
import time

import cv2

from common.zenoh_args import parse_zenoh_args

DEFAULT_PREFIX = "demo/obj-detect"
DEFAULT_WIDTH = 1024
DEFAULT_QUALITY = 80
DEFAULT_DELAY = 0.1
PI_FRAME_RATE = 90.0
PICAMERA_BUFFER_COUNT = 6


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="capture_video",
        description="Banane v2.0 camera capture",
    )
    parser.add_argument("-i", "--id", type=int, default=random.randint(1, 999))
    parser.add_argument(
        "-a",
        "--camera",
        default="default",
        choices=["default", "picamera"],
    )
    parser.add_argument("-w", "--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("-q", "--quality", type=int, default=DEFAULT_QUALITY)
    parser.add_argument("-d", "--delay", type=float, default=DEFAULT_DELAY)
    args, conf, _ = parse_zenoh_args(
        description="Publish JPEG camera frames over Zenoh",
        default_prefix=DEFAULT_PREFIX,
    )

    jpeg_opts = [int(cv2.IMWRITE_JPEG_QUALITY), args.quality]
    picamera = args.camera.startswith("picamera")
    cam_id = args.id
    resource_key = f"{args.prefix}/cams/{cam_id}"

    print("[INFO] Opening Zenoh session...")
    zenoh.init_log_from_env_or("error")
    z = zenoh.open(conf)

    latest_frame = None
    frame_lock = threading.Lock()
    frame_event = threading.Event()
    running = True

    def processing_thread(session, key, opts):
        while running:
            if not frame_event.wait(timeout=1.0):
                continue
            frame_event.clear()
            with frame_lock:
                frame = latest_frame
            if frame is None:
                continue
            try:
                success, jpeg = cv2.imencode(".jpg", frame, opts)
                if success:
                    session.put(key, jpeg.tobytes())
            except Exception as exc:
                print(f"[ERROR] Processing thread: {exc}")

    sender_thread = threading.Thread(
        target=processing_thread,
        args=(z, resource_key, jpeg_opts),
        daemon=True,
    )
    sender_thread.start()

    print(f"[INFO] Starting video stream - cam #{cam_id}")

    if picamera:
        from libcamera import Transform
        import picamera2

        vs = picamera2.Picamera2()
        height = int(args.width * 0.75)
        config = vs.create_video_configuration(
            main={"size": (args.width, height), "format": "RGB888"},
            controls={"FrameRate": PI_FRAME_RATE},
            transform=Transform(vflip=True),
        )
        config["buffer_count"] = PICAMERA_BUFFER_COUNT
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
                frame = imutils_resize(raw, args.width)

            with frame_lock:
                latest_frame = frame
            frame_event.set()

            time.sleep(args.delay)
    except KeyboardInterrupt:
        print("[INFO] Interrupted, shutting down...")
    finally:
        running = False
        sender_thread.join(timeout=2.0)
        vs.stop()
        z.close()
        print("[INFO] Stream stopped.")

    return 0


def imutils_resize(frame, width):
    """Lazily-imported wrapper around ``imutils.resize`` so we keep the
    optional USB-webcam dependency separate from the Pi-only path."""
    import imutils

    return imutils.resize(frame, width=width)


if __name__ == "__main__":
    sys.exit(main())
