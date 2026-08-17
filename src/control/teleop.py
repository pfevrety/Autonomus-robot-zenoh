"""Keyboard teleop using curses.

Arrow keys move the robot (linear on up/down, angular on left/right);
space stops; ESC / 'q' quits. The original example came from the ZettaScale
zenoh-ros-bridge samples and kept their license header.
"""

#
# Copyright (c) 2022 ZettaScale Technology Inc.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
#
# Contributors:
#   The Zenoh Team, <zenoh@zettascale.tech>
#

import argparse
import curses
import json

import zenoh

from common.publish import publish_twist
from common.topics import CMD_VEL
from common.types import Log, Time


def main(stdscr):
    stdscr.refresh()

    parser = argparse.ArgumentParser(
        prog="banane-teleop",
        description="Banane v2.0 keyboard teleop",
    )
    parser.add_argument("--mode", "-m", dest="mode", choices=["peer", "client"], type=str)
    parser.add_argument("--connect", "-e", dest="connect", action="append", type=str)
    parser.add_argument("--listen", "-l", dest="listen", action="append", type=str)
    parser.add_argument("--config", "-c", dest="config", type=str)
    parser.add_argument("--cmd_vel", dest="cmd_vel", default=CMD_VEL, type=str)
    parser.add_argument("--rosout", dest="rosout", default="rt/rosout", type=str)
    parser.add_argument("--angular_scale", "-a", dest="angular_scale", default="2.0", type=float)
    parser.add_argument("--linear_scale", "-x", dest="linear_scale", default="2.0", type=float)

    args = parser.parse_args()

    conf = zenoh.Config.from_file(args.config) if args.config else zenoh.Config()
    if args.mode:
        conf.insert_json5("mode", json.dumps(args.mode))
    if args.connect:
        conf.insert_json5("connect/endpoints", json.dumps(args.connect))
    if args.listen:
        conf.insert_json5("listen/endpoints", json.dumps(args.listen))

    cmd_vel = args.cmd_vel
    rosout = args.rosout
    angular_scale = args.angular_scale
    linear_scale = args.linear_scale

    zenoh.init_log_from_env_or("error")

    print("[INFO] Opening Zenoh session...")
    session = zenoh.open(conf)

    print(f"[INFO] Subscriber on '{rosout}'...")

    def rosout_callback(sample):
        log = Log.deserialize(sample.payload)
        print(
            "[{}.{}] [{}]: {}".format(
                log.stamp.sec, log.stamp.nanosec, log.name, log.msg
            )
        )

    sub = session.declare_subscriber(rosout, rosout_callback)

    print("[INFO] Use arrow keys to drive, space to stop, ESC / 'q' to quit.")
    while True:
        c = stdscr.getch()
        if c == curses.KEY_UP:
            publish_twist(session, 1.0 * linear_scale, 0.0, topic=cmd_vel)
        elif c == curses.KEY_DOWN:
            publish_twist(session, -1.0 * linear_scale, 0.0, topic=cmd_vel)
        elif c == curses.KEY_LEFT:
            publish_twist(session, 0.0, 1.0 * angular_scale, topic=cmd_vel)
        elif c == curses.KEY_RIGHT:
            publish_twist(session, 0.0, -1.0 * angular_scale, topic=cmd_vel)
        elif c == 32:
            publish_twist(session, 0.0, 0.0, topic=cmd_vel)
        elif c == 27 or c == ord("q"):
            break

    sub.undeclare()
    session.close()


curses.wrapper(main)
