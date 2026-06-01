import time
import cv2
import json
import zenoh
import numpy as np

conf = zenoh.Config()
cams = {}


def frames_listener(sample):
    chunks = str(sample.key_expr).split("/")
    cam = chunks[-1]
    if cam not in cams:
        cams[cam] = {}
    cams[cam]["img"] = bytes(sample.payload)


def objects_listener(sample):
    # print('[DEBUG] Received object: {} => {}'.format(sample.key_expr, sample.payload.decode("utf-8")))
    chunks = str(sample.key_expr).split("/")
    cam = chunks[-2]
    obj = int(chunks[-1])

    if cam not in cams:
        cams[cam] = {}
    if "objects" not in cams[cam]:
        cams[cam]["objects"] = {}
    if obj not in cams[cam]["objects"]:
        cams[cam]["objects"][obj] = {}

    cams[cam]["objects"][obj] = json.loads(sample.payload.to_string())
    cams[cam]["objects"][obj]["time"] = time.time()


print("[INFO] Open zenoh session...")

zenoh.init_log_from_env_or("error")
z = zenoh.open(conf)

z.declare_subscriber("demo/obj-detect/cams/*", frames_listener)
z.declare_subscriber("demo/obj-detect/objects/*/*", objects_listener)


def display_video_stream():
    while True:
        now = time.time()
        for cam in list(cams):
            if "img" in cams[cam]:
                npImage = np.frombuffer(cams[cam]["img"], dtype=np.uint8)
                matImage = cv2.imdecode(npImage, 1)
                if "objects" in cams[cam]:
                    for obj in list(cams[cam]["objects"]):
                        if cams[cam]["objects"][obj]["time"] > now - 0.2:

                            cv2.putText(
                                matImage,
                                cams[cam]["objects"][obj]["info"],
                                np.array(cams[cam]["objects"][obj]["box"][0]).astype(
                                    int
                                ),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (255, 0, 0),
                                2,
                            )
                            cv2.polylines(
                                matImage,
                                [
                                    np.array(cams[cam]["objects"][obj]["box"]).astype(
                                        int
                                    )
                                ],
                                True,
                                (255, 0, 0),
                                2,
                            )

                            cv2.putText(
                                matImage,
                                np.array(cams[cam]["objects"][obj]["center"])
                                .astype(int)
                                .tolist(),  # normaliser par rapport à la taille de l'image ?
                                np.array(cams[cam]["objects"][obj]["center"]).astype(
                                    int
                                ),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (255, 0, 0),
                                2,
                            )
                            cv2.circle(
                                matImage,
                                np.array(cams[cam]["objects"][obj]["center"]).astype(
                                    int
                                ),
                                5,
                                (0, 255, 0),
                                -1,
                            )

                _, jpeg_buffer = cv2.imencode(".jpg", matImage)

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + jpeg_buffer.tobytes()
                    + b"\r\n"
                )
                break

        time.sleep(0.03)
