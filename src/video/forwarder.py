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

    def remove_aimed_object(self, object_name):
        if object_name in self.aimed_object_list:
            self.aimed_object_list.remove(object_name)
            print(f"Removed {object_name} from aimed objects list")
    
    def remove_all_aimed_objects(self):
        self.aimed_object_list.clear()
        print("Cleared all aimed objects from the list")
        

    def destroy(self):
        self.sub.undeclare()
        self.session.close()
        
        
aim = Aim()
try:
    print("Started Forwarder Successfully")
    while True:
        time.sleep(0.01)
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    aim.destroy()
