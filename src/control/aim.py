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

        conf = zenoh.Config()

        zenoh.init_log_from_env_or("error")
        self.session = zenoh.open(conf)
        self.sub = self.session.declare_subscriber("robot/aimed", self.box_callback)
        self.sub = self.session.declare_subscriber(
            "robot/not_aimed", self.not_aimed_callback
        )
        self.aimed = 0.5
        self.last_time = -2.0

    def box_callback(self, sample: zenoh.Sample):
        self.last_time = time.time()
        data = json.loads(sample.payload.to_bytes())
        self.aimed = data.get("normalized_center")[0]

    def not_aimed_callback(self, sample: zenoh.Sample):
        self.last_time = time.time()
        self.aimed = 0.9

    def pub_twist(self, linear, angular):

        print("Pub twist: {} - {}".format(linear, angular))
        t = Twist(
            linear=Vector3(x=float(linear), y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=float(angular)),
        )
        self.session.put(self.cmd_vel_topic, t.serialize())

    def move(self):
        if time.time() - self.last_time > 0.4:
            return

        if abs(self.aimed - 0.5) <= self.deadzone / 2.0:
            self.pub_twist(0.0, 0.0)
        else:
            intensity = (abs(self.aimed - 0.5) - self.deadzone / 2.0) / (
                0.5 - self.deadzone / 2.0
            )

            if self.aimed > 0.5:
                self.pub_twist(0.0, intensity * self.angular_scale)
            else:
                self.pub_twist(0.0, -intensity * self.angular_scale)

    def destroy(self):
        self.sub.undeclare()
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
