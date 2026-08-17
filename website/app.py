"""FastAPI web dashboard for the Banane v2.0 robot.

Exposes:

- ``GET  /``             static dashboard (Tailwind + JS + custom CSS),
- ``GET  /video_feed``   MJPEG stream from the latest camera frame,
- ``GET  /stream``       Server-Sent Events for ``robot/aimed`` / found-object updates,
- ``POST /command``      translate an action string into a Twist command,
- ``POST /klaxon``       play a sound,
- ``POST /add_aimed_object``     add an object to the robot's target queue,
- ``POST /clear_aimed_objects``  clear the queue,
- ``POST /update_latency``       tune the aim loop latency (ms),
- ``POST /update_sensitivity``   tune the aim loop angular scale.

The app owns its own ``Forwarder`` instance so detection forwarding,
state publication, and the dashboard share the same Zenoh session.
"""

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from control.web_teleop import TeleopManager
from video.forwarder import Forwarder
from video.web_display_video import stream_first_camera

ANGULAR_SCALE = 200
LATENCY = 0.5

teleop = TeleopManager()
forwarder = Forwarder()

event_queue: asyncio.Queue = asyncio.Queue()
main_loop: asyncio.AbstractEventLoop | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    main_loop = asyncio.get_running_loop()

    def found_object_callback(sample):
        object_name = sample.payload.to_bytes().decode("utf-8", errors="ignore")
        print(f"[INFO] Object found: {object_name}")
        main_loop.call_soon_threadsafe(
            event_queue.put_nowait, {"event": "found", "object_name": object_name}
        )

    def aimed_callback(sample):
        print(f"[INFO] Aimed sample received: {sample.payload.to_string()}")
        try:
            data = json.loads(sample.payload.to_bytes())
            x_position = data.get("normalized_center")[0]
            main_loop.call_soon_threadsafe(
                event_queue.put_nowait, {"event": "aimed", "position": x_position}
            )
        except Exception as exc:
            print(f"[ERROR] Failed to parse aimed payload: {exc}")

    sub_aimed = forwarder.session.declare_subscriber("robot/aimed", aimed_callback)
    sub_found = forwarder.session.declare_subscriber(
        "robot/found_object", found_object_callback
    )

    yield

    print("[INFO] Stopping server")
    sub_aimed.undeclare()
    sub_found.undeclare()
    forwarder.destroy()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/video_feed")
def video_feed():
    print("[INFO] Client connected to video feed")
    return StreamingResponse(
        stream_first_camera("demo/obj-detect", forwarder.session),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/command")
async def receive_command(request: Request):
    data = await request.json()
    action = data.get("action")
    print(f"[INFO] Received command: {action}")
    teleop.handle_command(action)
    return {"status": "success", "action": action}


app.mount("/scripts", StaticFiles(directory="website/scripts"), name="script")
app.mount("/styles", StaticFiles(directory="website/styles"), name="style")


@app.post("/add_aimed_object")
async def add_aimed_object(request: Request):
    data = await request.json()
    object_name = data.get("object_name")
    if not object_name:
        return {"status": "error", "message": "No object name provided"}
    forwarder.add_aimed_object(object_name)
    return {
        "status": "success",
        "message": f"Added {object_name} to aimed objects list",
    }


@app.post("/clear_aimed_objects")
async def clear_aimed_objects():
    forwarder.remove_all_aimed_objects()
    return {"status": "success", "message": "Cleared all aimed objects from the list"}


@app.post("/update_latency")
async def update_latency(request: Request):
    data = await request.json()
    latency_ms = data.get("latency")
    if latency_ms is None:
        return {"status": "error", "message": "Missing latency value"}
    forwarder.session.put("robot/config/latency", str(latency_ms))
    return {"status": "success", "latency": latency_ms}


@app.post("/update_sensitivity")
async def update_sensitivity(request: Request):
    data = await request.json()
    sensitivity = data.get("sensitivity")
    if sensitivity is None:
        return {"status": "error", "message": "Missing sensitivity value"}
    forwarder.session.put("robot/config/sensitivity", str(sensitivity))
    return {"status": "success", "sensitivity": sensitivity}


@app.post("/klaxon")
async def activate_klaxon():
    print("[INFO] Klaxon requested via web")
    teleop.handle_command("bip")
    return {"status": "success", "action": "klaxon"}


@app.get("/stream")
async def stream_events():
    async def event_generator():
        while True:
            data = await event_queue.get()
            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/")
def serve_home():
    return FileResponse("website/templates/index.html")


if __name__ == "__main__":
    print("[INFO] Starting web server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
