"""Dynamixel driver: bridges Zenoh Twist messages to the XM430 servomotor.

Subscribes to ``rt/turtle1/cmd_vel`` (CDR-serialised ``Twist``) and
``rt/turtle1/klaxon`` (UTF-8 sound ID) and writes the corresponding
control-table registers on every loop iteration. Also publishes a
heartbeat counter on ``rt/turtle1/heartbeat`` for diagnostics.
"""

import argparse
import json
import sys
import time

import zenoh

from common.zenoh_args import parse_zenoh_args
from common.types import Twist, Vector3
from servo import (
    CMD_VELOCITY_ANGULAR_X,
    CMD_VELOCITY_ANGULAR_Y,
    CMD_VELOCITY_ANGULAR_Z,
    CMD_VELOCITY_LINEAR_X,
    CMD_VELOCITY_LINEAR_Z,
    HEARTBEAT,
    IMU_RE_CALIBRATION,
    SOUND,
    Servo,
)

DEVICENAME = "/dev/ttyACM0"
PROTOCOL_VERSION = 2.0
BAUDRATE = 115200
MOTOR_ID = 200

DEFAULT_DELAY = 0.01
DEFAULT_PREFIX = "rt/turtle1"
HEARTBEAT_ROLLOVER = 256  # heartbeat is a single byte on the bus.


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="zdrive",
        description="Banane v2.0 Dynamixel driver",
    )
    parser.add_argument("-d", "--delay", type=float, default=DEFAULT_DELAY)
    args, conf, _ = parse_zenoh_args(
        description="Zenoh bridge to the XM430 servomotor",
        default_prefix=DEFAULT_PREFIX,
        argv=None,
    )

    cmd = Twist(Vector3(0.0, 0.0, 0.0), Vector3(0.0, 0.0, 0.0))
    play_sound_flag = False

    print("[INFO] Opening Zenoh session...")
    zenoh.init_log_from_env_or("error")
    z = zenoh.open(conf)

    publ = z.declare_publisher(f"{args.prefix}/heartbeat")

    def listener(sample):
        nonlocal cmd
        cmd = Twist.deserialize(bytes(sample.payload))

    def klaxon_listener(sample):
        nonlocal play_sound_flag
        try:
            sound_id = int(sample.payload.to_string())
        except ValueError:
            sound_id = 1
        print(f"[INFO] Klaxon requested, sound ID {sound_id}")
        # Store the requested sound ID for the next loop iteration to pick up.
        klaxon_listener.sound_id = sound_id
        play_sound_flag = True

    klaxon_listener.sound_id = 1  # default sound

    print("[INFO] Connecting to motor...")
    servo = Servo(DEVICENAME, PROTOCOL_VERSION, BAUDRATE, MOTOR_ID)

    sub_cmd = z.declare_subscriber(f"{args.prefix}/cmd_vel", listener)
    sub_klaxon = z.declare_subscriber(f"{args.prefix}/klaxon", klaxon_listener)

    servo.write1ByteTxRx(IMU_RE_CALIBRATION, 1)

    time.sleep(3.0)
    print("[INFO] Running!")

    count = 0
    while True:
        servo.write1ByteTxRx(HEARTBEAT, count)

        if play_sound_flag:
            servo.write1ByteTxRx(HEARTBEAT, 0)
            servo.write4ByteTxRx(SOUND, klaxon_listener.sound_id)
            play_sound_flag = False

        servo.write4ByteTxRx(CMD_VELOCITY_LINEAR_X, int(cmd.linear.x))
        servo.write4ByteTxRx(CMD_VELOCITY_LINEAR_Z, int(cmd.linear.z))
        servo.write4ByteTxRx(CMD_VELOCITY_ANGULAR_X, int(cmd.angular.x))
        servo.write4ByteTxRx(CMD_VELOCITY_ANGULAR_Y, int(cmd.angular.y))
        servo.write4ByteTxRx(CMD_VELOCITY_ANGULAR_Z, int(cmd.angular.z))

        publ.put(str(count))

        count = (count + 1) % HEARTBEAT_ROLLOVER

        time.sleep(args.delay)

    return 0


if __name__ == "__main__":
    sys.exit(main())
