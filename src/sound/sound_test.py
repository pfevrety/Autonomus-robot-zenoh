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

time.sleep(3.0)

print("[INFO] Running!")
if servo is not None:
    print("Play ON")
    servo.write1ByteTxRx(HEARTBEAT, 0)
    servo.write4ByteTxRx(SOUND, 1)
    time.sleep(5)

    print("Play LOW_BATTERY")
    servo.write1ByteTxRx(HEARTBEAT, 0)
    servo.write4ByteTxRx(SOUND, 2)
    time.sleep(5)

    print("Play ERROR")
    servo.write1ByteTxRx(HEARTBEAT, 0)
    servo.write4ByteTxRx(SOUND, 3)
    time.sleep(5)

    print("Play OFF")
    servo.write1ByteTxRx(HEARTBEAT, 0)
    servo.write4ByteTxRx(SOUND, 0)
    time.sleep(5)

    print("Play OFF")
    servo.write1ByteTxRx(HEARTBEAT, 0)
    servo.write4ByteTxRx(SOUND, 4)
    time.sleep(5)

    print("Play OFF")
    servo.write1ByteTxRx(HEARTBEAT, 0)
    servo.write4ByteTxRx(SOUND, 5)
    time.sleep(5)
