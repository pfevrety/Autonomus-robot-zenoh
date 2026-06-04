import argparse
import time
import cv2
import json
import random
import zenoh
import numpy as np
from ultralytics import YOLO
from collections import deque
from statistics import median

parser = argparse.ArgumentParser(
    prog="detect", description="zenoh object detection example"
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
    "-d",
    "--delay",
    type=float,
    default=0.05,
    help="delay between each frame in seconds",
)
parser.add_argument(
    "-s",
    "--model-size",
    type=str,
    default="s",
    help="The size of the model to use. Can be 'n', 's', 'm', 'l' or 'x'.",
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

qcd = cv2.QRCodeDetector()
cams = {}
history_conf = {}
history_center = {}
model = YOLO("yolo26" + args.model_size + ".pt")


def frames_listener(sample):
    chunks = str(sample.key_expr).split("/")
    cam = chunks[-1]

    if cam not in cams:
        cams[cam] = {}

    cams[cam]["img"] = bytes(sample.payload)
    cams[cam]["img_time"] = time.time()


def smooth_detection(object_name, confidence):
    key = object_name

    if key not in history_conf:
        history_conf[key] = deque(maxlen=10)

    history_conf[key].append(confidence)

    return median(history_conf[key])


def smooth_center_quadratic(object_name, center, confidence):
    if object_name not in history_center:
        history_center[object_name] = deque(maxlen=10)

    history_center[object_name].append((center[0], center[1], confidence))

    points = list(history_center[object_name])

    weighted_x = 0
    weighted_y = 0
    total_weight = 0

    for i, (x, y, conf) in enumerate(points):
        time_weight = (i + 1) ** 2
        weight = time_weight * conf

        weighted_x += x * weight
        weighted_y += y * weight
        total_weight += weight

    if total_weight == 0:
        return center

    return [int(weighted_x / total_weight), int(weighted_y / total_weight)]


print("[INFO] Open zenoh session...")

zenoh.init_log_from_env_or("error")
z = zenoh.open(conf)

print("[INFO] Start detection")
sub = z.declare_subscriber(args.prefix + "/cams/*", frames_listener)

while True:
    now = time.time()
    for cam in list(cams):
        if "img_time" in cams[cam] and now - cams[cam]["img_time"] > 2.0:
            del cams[cam]
    for cam in list(cams):
        npImage = np.frombuffer(cams[cam]["img"], dtype=np.uint8)
        matImage = cv2.imdecode(npImage, 1)

        if matImage is None:
            continue

        results = model.predict(source=matImage, show_boxes=True, verbose=False)
        i = 0
        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:
                for data in box.data:
                    box = [
                        [int(data[0]), int(data[1])],
                        [int(data[2]), int(data[1])],
                        [int(data[2]), int(data[3])],
                        [int(data[0]), int(data[3])],
                    ]

                    confidence = float(data[4])
                    object_name = result.names[int(data[5])]

                    smoothed_confidence = smooth_detection(object_name, confidence)

                    center = [
                        int((data[0] + data[2]) / 2),
                        int((data[1] + data[3]) / 2),
                    ]

                    smoothed_center = smooth_center_quadratic(
                        object_name, center, smoothed_confidence
                    )
                    hauteur, largeur = matImage.shape[:2]
                    z.put(
                        "{}/objects/{}/{}".format(args.prefix, cam, i),
                        json.dumps(
                            {
                                "name": object_name,
                                "confiance": int(smoothed_confidence * 100),
                                "box": box,
                                "raw_center": center,
                                "center": smoothed_center,
                                "normalized_center": [
                                    smoothed_center[0] / largeur,
                                    smoothed_center[1] / hauteur,
                                ],
                            }
                        ),
                    )
                    i += 1

    # time.sleep(args.delay)

vs.stop()
z.close()
