import zenoh
from control.common import *

class TeleopManager:
    def __init__(
        self, cmd_vel_topic="rt/turtle1/cmd_vel", linear_scale=20.0, angular_scale=200.0
    ):
        self.cmd_vel_topic = cmd_vel_topic
        self.angular_scale = angular_scale
        self.linear_scale = linear_scale

        conf = zenoh.Config()

        zenoh.init_log_from_env_or("error")
        self.session = zenoh.open(conf)

    def pub_twist(self, linear, angular):

        print("Pub twist: {} - {}".format(linear, angular))
        t = Twist(
            linear=Vector3(x=float(linear), y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=float(angular)),
        )
        self.session.put(self.cmd_vel_topic, t.serialize())

    def handle_command(self, action):
        if action == "move_haut":
            self.pub_twist(1.0 * self.linear_scale, 0.0)
        elif action == "move_bas":
            self.pub_twist(-1.0 * self.linear_scale, 0.0)
        elif action == "move_gauche":
            self.pub_twist(0.0, 1.0 * self.angular_scale)
        elif action == "move_droite":
            self.pub_twist(0.0, -1.0 * self.angular_scale)
        elif action == "stop":
            self.pub_twist(0.0, 0.0)
