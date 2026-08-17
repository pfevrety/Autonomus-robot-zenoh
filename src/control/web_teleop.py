"""HTTP-driven teleop bridge.

The web UI (``website/app.py``) POSTs human-readable action strings
(``move_up``, ``klaxon``, ...) to ``/command``; this module translates them
into the same ``Twist`` / klaxon payloads as the keyboard teleop.
"""

from __future__ import annotations

import zenoh

from common.publish import publish_klaxon, publish_twist
from common.topics import CMD_VEL, KLAXON


class TeleopManager:
    def __init__(
        self,
        cmd_vel_topic: str = CMD_VEL,
        linear_scale: float = 20.0,
        angular_scale: float = 200.0,
    ):
        self.cmd_vel_topic = cmd_vel_topic
        self.klaxon_topic = KLAXON
        self.angular_scale = angular_scale
        self.linear_scale = linear_scale

        conf = zenoh.Config()
        zenoh.init_log_from_env_or("error")
        print("[INFO] Opening Zenoh session...")
        self.session = zenoh.open(conf)

    def handle_command(self, action: str) -> None:
        if action == "move_up":
            publish_twist(self.session, -1.0 * self.linear_scale, 0.0, topic=self.cmd_vel_topic)
        elif action == "move_down":
            publish_twist(self.session, 1.0 * self.linear_scale, 0.0, topic=self.cmd_vel_topic)
        elif action == "move_left":
            publish_twist(self.session, 0.0, 1.0 * self.angular_scale, topic=self.cmd_vel_topic)
        elif action == "move_right":
            publish_twist(self.session, 0.0, -1.0 * self.angular_scale, topic=self.cmd_vel_topic)
        elif action == "stop":
            publish_twist(self.session, 0.0, 0.0, topic=self.cmd_vel_topic)
        elif action == "bip":
            publish_klaxon(self.session, sound_id=3, topic=self.klaxon_topic)
        else:
            print(f"[WARN] Unknown teleop action: {action}")
