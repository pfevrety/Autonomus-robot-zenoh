# forwarder.py
import zenoh
import json
import time

class Aim:
    def __init__(self):
        conf = zenoh.Config()
        zenoh.init_log_from_env_or("error")
        self.session = zenoh.open(conf)
        self.sub = self.session.declare_subscriber("**/objects/**", self.objects_callback)
        self.aimed_object_list = []
        
    def objects_callback(self, sample: zenoh.Sample):
        self.last_time = time.time()
        data = json.loads(sample.payload.to_bytes())
        if data.get("name") in self.aimed_object_list:
            print("Forwarding")
            self.session.put("robot/aimed", sample.payload)

    def add_aimed_object(self, object_name):
        if object_name not in self.aimed_object_list:
            self.aimed_object_list.append(object_name)
            print(f"Added {object_name} to aimed objects list")

    def destroy(self):
        self.sub.undeclare()
        self.session.close()
        
        
aim = Aim()

if __name__ == "__main__":
    print("Starting in standalone mode...")
    try:
        print("Started Forwarder Successfully")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        aim.destroy()