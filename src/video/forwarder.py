"""Detection forwarder.

Bridges every YOLO detection on the ``demo/obj-detect/objects/*/*`` topic
to the ``robot/aimed`` topic, but only when the detection's ``name``
matches the user's currently-targeted object. Also maintains the
``robot/state`` flag (``True`` when there is at least one objective)
and removes an objective from the queue when the robot reports having
found the corresponding object on ``robot/found_object``.
"""

from __future__ import annotations

import json
import sys
import time

import zenoh

from common.topics import (
    OBJ_DETECT_OBJECTS_PATTERN,
    ROBOT_AIMED,
    ROBOT_FOUND_OBJECT,
    ROBOT_STATE,
)


class Forwarder:
    def __init__(self):
        conf = zenoh.Config()
        zenoh.init_log_from_env_or("error")
        self.session = zenoh.open(conf)

        self.sub = self.session.declare_subscriber(
            OBJ_DETECT_OBJECTS_PATTERN, self.objects_callback
        )
        self.sub_found_object = self.session.declare_subscriber(
            ROBOT_FOUND_OBJECT, self.found_object_callback
        )

        self.aimed_object_list: list[str] = []
        self._update_state()

    def _update_state(self):
        state = bytes(bool(self.aimed_object_list))
        self.session.put(ROBOT_STATE, state)

    def objects_callback(self, sample: zenoh.Sample):
        data = json.loads(sample.payload.to_bytes())

        if (
            self.aimed_object_list
            and data.get("name") == self.aimed_object_list[0]
        ):
            # Re-publish verbatim: aim.py expects the JSON payload structure.
            self.session.put(ROBOT_AIMED, sample.payload)

    def add_aimed_object(self, object_name: str) -> None:
        if object_name in self.aimed_object_list:
            print(f"[INFO] {object_name} already in the aimed list")
            return
        self.aimed_object_list.append(object_name)
        print(f"[INFO] Added {object_name} to aimed objects list")
        self._update_state()

    def remove_aimed_object(self, object_name: str) -> None:
        if object_name in self.aimed_object_list:
            self.aimed_object_list.remove(object_name)
            print(f"[INFO] Removed {object_name} from aimed objects list")
            self._update_state()
        else:
            print(f"[WARN] Could not find object with name {object_name}")

    def remove_all_aimed_objects(self) -> None:
        self.aimed_object_list.clear()
        print("[INFO] Cleared all aimed objects from the list")
        self._update_state()

    def found_object_callback(self, sample: zenoh.Sample):
        print(f"[INFO] Removing {sample.payload.to_string()}")
        self.remove_aimed_object(sample.payload.to_string())

    def destroy(self) -> None:
        self.sub.undeclare()
        self.sub_found_object.undeclare()
        self.session.close()


if __name__ == "__main__":
    forwarder = Forwarder()
    try:
        print("[INFO] Forwarder started successfully")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("[INFO] Shutting down...")
    finally:
        forwarder.destroy()

    sys.exit(0)
