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
        self.latency = 1
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

        if self.robot_state == AimState.SEARCHING and abs(self.aimed - 0.5) < self.deadzone / 2:
            pass #advance or beep
            #check for size -> if big enough -> beep
            #               -> if not big enough -> advance (handle disappearing objects)

    def move(self):
        if self.robot_state == AimState.STOPPED:
            return

        if time.time() - self.last_moved_time < self.latency: #waiting for latency before moving again
            return

        if self.robot_state == AimState.SEARCHING:
            self.aimed = 0.9
        
        intensity = (abs(self.aimed - 0.5)) / (0.5 + self.deadzone / 2.0)
        sign = 1 if self.aimed > 0.5 else -1

        self.pub_twist(0.0, sign * intensity * self.angular_scale)
        self.last_moved_time = time.time()

    def pub_twist(self, linear, angular):
        if angular == 0 and linear == 0:
            return
        
        print("\nmove", linear, angular)

        self.robot_state = AimState.STOPPED

        t = Twist(
            linear=Vector3(x=float(linear), y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=float(angular))
        )

        self.session.put(self.cmd_vel_topic, t.serialize())
    
    def update(self):
        self.move()
        time.sleep(0.01)
    
    def found_object(self):
        self.robot_state = AimState.STOPPED

        self.session.put("rt/turtle1/klaxon", str(1).encode("utf-8"))
        self.session.put("robot/found_object", self.searched_object.encode())

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
