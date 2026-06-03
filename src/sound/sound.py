import time
import io
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "motor"))
from servo import *

DEVICENAME = "/dev/ttyACM0"
PROTOCOL_VERSION = 2.0
BAUDRATE = 115200
MOTOR_ID = 200

print("[INFO] Connect to OpenCR...")
servo = Servo(DEVICENAME, PROTOCOL_VERSION, BAUDRATE, MOTOR_ID)
if servo is None:
    print("[WARN] Unable to connect to OpenCR.")
else:
    servo.write1ByteTxRx(IMU_RE_CALIBRATION, 1)
print("[INFO] Running!")


def play_sound(sound_id):
    if servo is not None:
        servo.write1ByteTxRx(HEARTBEAT, 0)
        servo.write4ByteTxRx(SOUND, sound_id)


def play_on():
    print("Play ON")
    play_sound(1)


def play_error():
    print("Play ERROR")
    play_sound(3)


def play_bip():
    print("Play Bip")
    play_sound(3)


def play_off():
    print("Play OFF")
    play_sound(0)
