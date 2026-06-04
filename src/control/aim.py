import zenoh
from common import *
import json
import time


class Aim:
    def __init__(
        self, cmd_vel_topic="rt/turtle1/cmd_vel", linear_scale=20.0, angular_scale=200.0
    ):
        self.cmd_vel_topic = cmd_vel_topic
        self.angular_scale = angular_scale
        self.linear_scale = linear_scale
        self.deadzone = 0.2
        self.latency = 2

        conf = zenoh.Config()
        zenoh.init_log_from_env_or("error")
        self.session = zenoh.open(conf)

        self.sub = self.session.declare_subscriber("robot/aimed", self.box_callback)
        self.sub_state = self.session.declare_subscriber(
            "robot/state", self.state_callback
        )
        self.sub_lat = self.session.declare_subscriber(
            "robot/config/latency", self.latency_callback
        )
        self.sub_sens = self.session.declare_subscriber(
            "robot/config/sensitivity", self.sensitivity_callback
        )

        self.aimed = 2.0
        self.robot_state = "WAIT"

        self.last_action_time = time.time()

    def state_callback(self, sample: zenoh.Sample):
        self.robot_state = sample.payload.to_bytes().decode("utf-8")
        self.aimed = 2.0
        self.last_action_time = time.time()
        print(f"État du robot mis à jour: {self.robot_state}")

        self.object_width = 0.0

        self.forward_speed = 0.5
        self.forward_duration = 0.3
        self.is_moving_forward = False
        self.forward_start_time = 0.0

    def latency_callback(self, sample: zenoh.Sample):
        self.latency = float(sample.payload.to_bytes().decode("utf-8")) / 1000
        print(f"Latence mise à jour: {self.latency}s")

    def sensitivity_callback(self, sample: zenoh.Sample):
        self.angular_scale = float(sample.payload.to_bytes().decode("utf-8"))
        print(f"Sensibilité mise à jour: {self.angular_scale}")

    def box_callback(self, sample: zenoh.Sample):
        current_time = time.time()
        if current_time - self.last_action_time < self.latency:
            return

        self.last_action_time = current_time

        data = json.loads(sample.payload.to_bytes())
        self.aimed = data.get("normalized_center")[0]
        self.searched_object = data.get("name")
        self.object_width = data.get("normalized_width", 0.0)

    def not_box_callback(self):
        current_time = time.time()
        if current_time - self.last_action_time < self.latency * 1.2:
            return

        self.last_action_time = current_time

        self.aimed = 0.9

    def move(self):
        if self.aimed == 2.0:
            if self.robot_state == "SEARCHING":
                self.not_box_callback()
            else:
                return
        if time.time() - self.last_action_time > 0.4:
            return
        if self.aimed == 2.0:
            return
        elif abs(self.aimed - 0.5) <= self.deadzone / 2.0:
            self.found_object()
        else:
            intensity = (abs(self.aimed - 0.5)) / (0.5 + self.deadzone / 2.0)

        if self.is_moving_forward:
            if current_time - self.forward_start_time < self.forward_duration:
                self.pub_twist(self.forward_speed, 0.0)
                return
            else:
                self.pub_twist(0.0, 0.0)
                self.is_moving_forward = False
                return

        if abs(self.aimed - 0.5) <= self.deadzone / 2.0:
            self.is_moving_forward = True
            self.forward_start_time = current_time
            self.pub_twist(self.forward_speed, 0.0)
            return

        intensity = (abs(self.aimed - 0.5) - self.deadzone / 2.0) / (
            0.5 - self.deadzone / 2.0
        )

        if self.aimed > 0.5:
            self.pub_twist(0.0, intensity * self.angular_scale)
        else:
            self.pub_twist(0.0, -intensity * self.angular_scale)

    def pub_twist(self, linear, angular):
        if angular == 0 and linear == 0:
            return
        print("\nmove", linear, angular)

        self.aimed = 2.0
        t = Twist(
            linear=Vector3(x=float(linear), y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=float(angular)),
        )
        self.session.put(self.cmd_vel_topic, t.serialize())
        return

    def found_object(self):
        self.aimed = 2.0
        self.session.put("rt/turtle1/klaxon", str(1).encode("utf-8"))
        self.session.put("robot/found_object", self.searched_object.encode("utf-8"))

    def destroy(self):
        self.sub.undeclare()
        self.sub_state.undeclare()
        self.sub_lat.undeclare()
        self.sub_sens.undeclare()
        self.session.close()


print("Starting...")
aim = Aim()

try:
    print("Started Aim Successfully")
    while True:
        aim.move()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    aim.destroy()
