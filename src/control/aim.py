import zenoh
from common import *
import json
import time
from aimstate import AimState

STOP_SIZE = 0.6
DEFAULT_LINEAR_SCALE = 20.0
DEFAULT_ANGULAR_SCALE = 200.0
DEFAULT_ADVANCE_TIME = 0.8
DEFAULT_TURNING_TIME = 0.1
SEARCH_AGAIN_TIME = 1.5
BEEP_WAIT = 6.0
DEADZONE = 0.2
DEFAULT_LATENCY = 2.0

class Aim:
    def __init__(
        self, cmd_vel_topic="rt/turtle1/cmd_vel", linear_scale=DEFAULT_LINEAR_SCALE, angular_scale=DEFAULT_ANGULAR_SCALE
    ):
        self.cmd_vel_topic = cmd_vel_topic
        self.angular_scale = angular_scale
        self.linear_scale = linear_scale
        self.deadzone = DEADZONE
        self.latency = DEFAULT_LATENCY
        self.aimed = 0.5
        self.robot_state = AimState.STOPPED
        self.last_moved_time = time.time()
        self.last_received_time = time.time()
        self.last_twist = Twist(
            linear=Vector3(x=0.0, y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=0.0)
        )
        self.execute_time = 0.0
        self.intensity = 0.0

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
            self.last_moved_time = time.time()
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

        self.last_received_time = time.time()
        
        if abs(self.aimed - 0.5) < self.deadzone / 2:
            box = data.get("normalized_box")
            normalized_width = abs(box[1][0] - box[0][0])
            normalized_height = abs(box[0][1] - box[3][1])

            print(f"normalized width {normalized_width}, normalized height {normalized_height},\n box {box}")

            if normalized_width > STOP_SIZE or normalized_height > STOP_SIZE:
                self.robot_state = AimState.STOPPED
                self.do_twist(0.0, 0.0, 1.0) # pause immediately even though there's a time.sleep
                # self.send_twist()
                time.sleep(BEEP_WAIT / 2) # Wait for Beep Port to be available
                self.session.put("rt/turtle1/klaxon", str(1).encode("utf-8"))
                time.sleep(BEEP_WAIT / 2)
                self.session.put("robot/found_object", self.searched_object.encode())
            else:
                self.robot_state = AimState.ADVANCING
                self.intensity = 1 - max(normalized_width, normalized_height)

            pass #advance or beep
            #check for size -> if big enough -> beep
            #               -> if not big enough -> advance (handle disappearing objects)
        else:
            self.robot_state = AimState.AIMING
            self.intensity = (abs(self.aimed - 0.5)) / (0.5 + self.deadzone / 2.0)

    def choose_move_order(self):

        if self.robot_state == AimState.STOPPED:
            self.do_twist(0.0, 0.0, 1.0)    

        now = time.time()

        if now - self.last_moved_time < self.latency: #waiting for latency before moving again
            return
        
        if now - self.last_received_time > self.latency + SEARCH_AGAIN_TIME and (self.robot_state == AimState.AIMING or self.robot_state == AimState.ADVANCING):
            self.robot_state = AimState.SEARCHING

        if self.robot_state == AimState.SEARCHING:
            self.do_twist(0.0, self.angular_scale, DEFAULT_TURNING_TIME * 4)

        if self.robot_state == AimState.AIMING:
            sign = 1 if self.aimed > 0.5 else -1
            self.do_twist(0.0, sign * self.intensity * self.angular_scale, DEFAULT_TURNING_TIME)


        if self.robot_state == AimState.ADVANCING:
            self.do_twist(-self.linear_scale, 0.0, DEFAULT_ADVANCE_TIME * self.intensity)

        self.last_moved_time = now

    def do_twist(self, linear, angular, execute_time):
        self.execute_time = execute_time
        if not(angular == 0 and linear == 0):
            print("\nmove order", linear, angular)

        self.last_twist = Twist(
            linear=Vector3(x=float(linear), y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=float(angular))
        )


    def send_twist(self):
        if time.time() - self.last_moved_time < self.execute_time: #waiting for latency before moving again
            self.session.put(self.cmd_vel_topic, self.last_twist.serialize())
    
    def update(self):
        self.choose_move_order()
        self.send_twist()
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
