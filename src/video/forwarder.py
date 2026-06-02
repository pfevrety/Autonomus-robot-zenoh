#checks whether or not the correct object is identified and forwards it over to aim.py

import zenoh
import json
import time


class Aim:
    def __init__(self, aimed_object_name="banana"):
        conf = zenoh.Config()

        zenoh.init_log_from_env_or("error")
        self.session = zenoh.open(conf)
        self.sub = self.session.declare_subscriber("**/objects/**", self.objects_callback)
        self.aimed_object_name = aimed_object_name
        
    def objects_callback(self, sample: zenoh.Sample):
        self.last_time = time.time()
        data = json.loads(sample.payload.to_bytes())
        if data.get("name") == self.aimed_object_name:
            print("Forwarding")
            self.session.put("robot/aimed", sample.payload)

    def destroy(self):
        self.sub.undeclare()
        self.session.close()


print("Starting...")
aim = Aim()
try:
    print("Started Forwarder Successfully")
    while True:
        time.sleep(0.01)
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    aim.destroy()
