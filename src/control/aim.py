import zenoh
from common import *
import json
import time
from aimstate import AimState

class Aim:
    def __init__(
        self, cmd_vel_topic="rt/turtle1/cmd_vel", linear_scale=20.0, angular_scale=200.0
    ):
        self.cmd_vel_topic = cmd_vel_topic
        self.angular_scale = angular_scale
        self.linear_scale = linear_scale
        self.deadzone = 0.2
        self.latency = 2.5
        self.aimed = 0.5
        self.robot_state = AimState.STOPPED
        self.last_moved_time = time.time()

        self.searched_object = ""

        conf = zenoh.Config()
        zenoh.init_log_from_env_or("error")

        self.session = zenoh.open(conf)

        self.sub = self.session.declare_subscriber("robot/aimed", self.box_callback)
        self.sub_state = self.session.declare_subscriber("robot/state", self.state_callback)
        self.sub_lat = self.session.declare_subscriber("robot/config/latency", self.latency_callback)
        self.sub_sens = self.session.declare_subscriber("robot/config/sensitivity", self.sensitivity_callback)        

    def state_callback(self, sample: zenoh.Sample):
        if sample.payload.to_bytes(): #check for true or false (technically checking if null or not, but it's the same)
            self.robot_state = AimState.SEARCHING
        else:
            self.robot_state = AimState.STOPPED
        print(f"État du robot mis à jour à distance: {self.robot_state}")

    def latency_callback(self, sample: zenoh.Sample):
        self.latency = float(sample.payload.to_string()) / 1000
        print(f"Latence mise à jour: {self.latency}s")

    def sensitivity_callback(self, sample: zenoh.Sample):
        self.angular_scale = float(sample.payload.to_string())
        print(f"Angular Scale mis à jour: {self.angular_scale}")

    def box_callback(self, sample: zenoh.Sample):
        data = json.loads(sample.payload.to_bytes())
        self.searched_object = data.get("name")
        self.aimed = data.get("normalized_center")[0]

        
        if abs(self.aimed - 0.5) < self.deadzone / 2:
            box = data.get("normalized_box")
            normalized_width = abs(box[1][0] - box[0][0])
            normalized_height = abs(box[0][1] - box[3][1])

            print(f"normalized width {normalized_width}, normalized height {normalized_height},\n box {box}")

            if normalized_width > 0.7 or normalized_height > 0.7:
                self.robot_state = AimState.STOPPED
                self.session.put("rt/turtle1/klaxon", str(1).encode("utf-8"))
                self.session.put("robot/found_object", self.searched_object.encode())
            else:
                self.robot_state = AimState.ADVANCING

            pass #advance or beep
            #check for size -> if big enough -> beep
            #               -> if not big enough -> advance (handle disappearing objects)
        else:
            self.robot_state = AimState.AIMING

    def move(self):
        if self.robot_state == AimState.STOPPED:
            return

        if time.time() - self.last_moved_time < self.latency: #waiting for latency before moving again
            return

        if self.robot_state == AimState.SEARCHING:
            self.aimed = 0.9

        if self.robot_state == AimState.AIMING or self.robot_state == AimState.SEARCHING:
            intensity = (abs(self.aimed - 0.5)) / (0.5 + self.deadzone / 2.0)
            sign = 1 if self.aimed > 0.5 else -1

            self.pub_twist(0.0, sign * intensity * self.angular_scale)

        if self.robot_state == AimState.ADVANCING:
            self.pub_twist(self.linear_scale, 0.0)


        self.last_moved_time = time.time()

    def pub_twist(self, linear, angular):
        if angular == 0 and linear == 0:
            return
        
        print("\nmove", linear, angular)

        t = Twist(
            linear=Vector3(x=float(linear), y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=float(angular))
        )

        self.session.put(self.cmd_vel_topic, t.serialize())
    
    def update(self):
        self.move()
        time.sleep(0.01)

    def destroy(self):
        self.sub.undeclare()
        self.sub_state.undeclare()
        self.sub_lat.undeclare()
        self.sub_sens.undeclare()
        self.session.close()


if __name__ == "__main__":
    print("Starting Aim...")
    aim = Aim()
    try:
        print("Started Aim Successfully")
        while True:
            aim.update()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        aim.destroy()
