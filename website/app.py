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

from sound.sound import play_sound
from video.web_display_video import display_video_stream
from control.web_teleop import TeleopManager

process_detection = None
teleop = TeleopManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global process_detection

    print("[INFO] subprocess detect_objects.py started...")
    process_detection = subprocess.Popen(
        ["python", "./src/video/detect_objects.py", "-e", "tcp/127.0.0.1:7447"],
        shell=False,
    )

    yield

    print("\n[INFO] stopping server")

    # try:
    #     aim.destroy()
    #     print("[INFO] Zenoh subscriber destroyed safely.")
    # except Exception as e:
    #     print(f"[ERROR] Failed to destroy Zenoh session: {e}")

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
        payload = json.dumps({"action": "add", "object_name": object_name})
        teleop.session.put("robot/config/aimed_objects", payload.encode('utf-8'))
        
        return {"status": "success", "message": f"Sent command to add {object_name}"}
    else:
        return {"status": "error", "message": "No object name provided"}

@app.post("/clear_aimed_objects")
async def clear_aimed_objects():
    payload = json.dumps({"action": "clear"})
    teleop.session.put("robot/config/aimed_objects", payload.encode('utf-8'))
    return {"status": "success", "message": "Sent command to clear all aimed objects"}
@app.post("/klaxon")
async def activate_klaxon():
    print("[INFO] Klaxon activated!")
    play_sound(1)
    return {"status": "success", "action": "klaxon"}

@app.get("/")
def serve_home():
    return FileResponse("website/templates/index.html")


if __name__ == "__main__":
    print("[INFO] starting web server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
