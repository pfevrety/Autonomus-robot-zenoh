import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys
import subprocess
from contextlib import asynccontextmanager
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


from video.web_display_video import display_video_stream
from control.web_teleop import TeleopManager

# --- IMPORT AIM HERE ---
# Adjust the import path depending on where aim.py is located.
# If it's in the same directory, use: from aim import aim
import video.forwarder

process_detection = None
teleop = TeleopManager()
ANGULAR_SCALE = 120
LATENCY = 0.5


@asynccontextmanager
async def lifespan(app: FastAPI):
    global process_detection

    print("[INFO] subprocess detect_objects.py started...")
    # process_detection = subprocess.Popen(
    #     ["python", "./src/video/detect_objects.py", "-e", "tcp/127.0.0.1:7447"],
    #     shell=False,
    # )

    yield

    print("\n[INFO] stopping server")

    if process_detection:
        process_detection.terminate()
        print("\n[INFO] subprocess detect_objects.py terminated")
        process_detection.wait()


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
        display_video_stream(), media_type="multipart/x-mixed-replace; boundary=frame"
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

    if object_name:
        video.forwarder.aim.add_aimed_object(object_name)
        return {
            "status": "success",
            "message": f"Added {object_name} to aimed objects list",
        }
    else:
        return {"status": "error", "message": "No object name provided"}


@app.post("/clear_aimed_objects")
async def clear_aimed_objects():
    video.forwarder.aim.remove_all_aimed_objects()
    return {"status": "success", "message": "Cleared all aimed objects from the list"}


@app.post("/update_latency")
async def update_latency(request: Request):
    global LATENCY
    data = await request.json()
    LATENCY = data.get("latency")

    if LATENCY is not None:
        video.forwarder.aim.session.put("robot/config/latency", str(LATENCY))
        return {"status": "success", "latency": LATENCY}
    return {"status": "error", "message": "Valeur manquante"}


@app.post("/update_sensitivity")
async def update_sensitivity(request: Request):
    global ANGULAR_SCALE
    data = await request.json()
    ANGULAR_SCALE = data.get("sensitivity")

    if ANGULAR_SCALE is not None:
        video.forwarder.aim.session.put("robot/config/sensitivity", str(ANGULAR_SCALE))
        return {"status": "success", "sensitivity": ANGULAR_SCALE}
    return {"status": "error", "message": "Valeur manquante"}


@app.post("/klaxon")
async def activate_klaxon():
    print("[INFO] Klaxon command via Zenoh requested")
    teleop.pub_bip(1)
    return {"status": "success", "action": "klaxon"}


@app.get("/")
def serve_home():
    return FileResponse("website/templates/index.html")


if __name__ == "__main__":
    print("[INFO] starting web server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
