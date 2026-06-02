import zenoh
from control.common import *


class TeleopManager:
    def __init__(
        self,
        cmd_vel_topic="rt/turtle1/cmd_vel",
        rosout="rt/rosout",
        linear_scale=20.0,
        angular_scale=200.0,
    ):
        self.cmd_vel_topic = cmd_vel_topic
        self.rosout = rosout
        self.angular_scale = angular_scale
        self.linear_scale = linear_scale

        conf = zenoh.Config()
        zenoh.init_log_from_env_or("error")
        print("Openning session...")
        self.session = zenoh.open(conf)
        print("Subscriber on '{}'...".format(self.rosout))

    def pub_twist(self, linear, angular):

        print("Pub twist: {} - {}".format(linear, angular))
        t = Twist(
            linear=Vector3(x=float(linear), y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=float(angular)),
        )
        self.session.put(self.cmd_vel_topic, t.serialize())

    def handle_command(self, action):
        if action == "move_up":
            self.pub_twist(-1.0 * self.linear_scale, 0.0)
        elif action == "move_down":
            self.pub_twist(1.0 * self.linear_scale, 0.0)
        elif action == "move_left":
            self.pub_twist(0.0, 1.0 * self.angular_scale)
        elif action == "move_right":
            self.pub_twist(0.0, -1.0 * self.angular_scale)
        elif action == "stop":
            self.pub_twist(0.0, 0.0)
