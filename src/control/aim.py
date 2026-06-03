import zenoh
from common import *
import json
import time


class Aim:
    def __init__(
        self, cmd_vel_topic="rt/turtle1/cmd_vel", linear_scale=20.0, angular_scale=20.0
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
        self.sub2 = self.session.declare_subscriber(
            "robot/not_aimed", self.not_aimed_callback
        )
        self.sub3 = self.session.declare_subscriber(
            "robot/nothing_to_aimed", self.nothing_to_aimed_callback
        )

        self.sub_lat = self.session.declare_subscriber(
            "robot/config/latency", self.latency_callback
        )
        self.sub_sens = self.session.declare_subscriber(
            "robot/config/sensitivity", self.sensitivity_callback
        )

        self.aimed = 0.5
        self.last_action_time = time.time()
        self.last_movement = time.time()
        self.last_time = 0.0

    def latency_callback(self, sample: zenoh.Sample):
        self.latency = float(sample.payload.to_bytes().decode("utf-8")) / 1000
        print(f"Latence mise à jour: {self.latency}s")

    def sensitivity_callback(self, sample: zenoh.Sample):
        self.angular_scale = float(sample.payload.to_bytes().decode("utf-8"))
        print(f"Sensibilité mise à jour: {self.angular_scale}")

    def box_callback(self, sample: zenoh.Sample):
        current_time = time.time()
        # print("AIIIIIMED")

        # self.last_time = current_time

        # self.aimed_time = time.time()
        print(current_time - self.last_action_time, self.latency)
        if current_time - self.last_action_time < self.latency:
            self.aimed = 0.5
            return

        self.last_action_time = current_time
        data = json.loads(sample.payload.to_bytes())
        self.aimed = data.get("normalized_center")[0]
        # print("AIIIIIMED", self.aimed, data.get("normalized_center")[0])

    def not_aimed_callback(self, sample: zenoh.Sample):
        #     current_time = time.time()
        #     self.last_time = current_time
        #     if current_time - self.aimed_time > 0.1:
        #         return
        #     if 0.05 < current_time - self.last_action_time < self.latency:
        #         self.aimed = 0.5
        #         return
        #     print("NOOOOOOOOOOOOO")
        #     self.last_action_time = current_time
        #     self.aimed = 0.9
        self.aimed = 0.5

    def nothing_to_aimed_callback(self, sample: zenoh.Sample):
        #     current_time = time.time()
        #     self.last_time = current_time
        #     print("nta")
        self.aimed = 0.5

    def pub_twist(self, linear, angular):
        current_time = time.time()
        if angular == 0 and linear == 0:
            return
        if current_time - self.last_movement < 0.1:
            return
        self.last_movement = current_time
        print("move", linear, angular)
        return
        t = Twist(
            linear=Vector3(x=float(linear), y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=float(angular)),
        )
        self.session.put(self.cmd_vel_topic, t.serialize())
        return

    def move(self):

        # if time.time() - self.last_time > self.latency + 0.4:
        #     return

        if abs(self.aimed - 0.5) <= self.deadzone / 2.0:
            self.pub_twist(0.0, 0.0)
        else:
            intensity = (abs(self.aimed - 0.5) - self.deadzone / 2.0) / (
                0.5 - self.deadzone / 2.0
            )
            # print(intensity)

            if self.aimed > 0.5:
                self.pub_twist(0.0, intensity * self.angular_scale)
            else:
                self.pub_twist(0.0, -intensity * self.angular_scale)

    def destroy(self):
        # On nettoie proprement les souscriptions
        self.sub.undeclare()
        self.sub2.undeclare()
        self.sub3.undeclare()
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
