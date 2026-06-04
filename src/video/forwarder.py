import zenoh
import json
import time

class Forwarder:
    def __init__(self):
        conf = zenoh.Config()
        zenoh.init_log_from_env_or("error")
        self.session = zenoh.open(conf)

        self.sub = self.session.declare_subscriber("**/objects/**", self.objects_callback)
        self.sub_found_object = self.session.declare_subscriber("robot/found_object", self.found_object_callback)
        
        self.aimed_object_list = []
        self.update_state()

    def update_state(self):
        state = True if len(self.aimed_object_list) > 0 else False
        self.session.put("robot/state", bytes(state))

    def objects_callback(self, sample: zenoh.Sample):
        data = json.loads(sample.payload.to_bytes())
        if len(self.aimed_object_list) > 0 and data.get("name") == self.aimed_object_list[0]:
            self.session.put("robot/aimed", sample.payload)

    def add_aimed_object(self, object_name):
        if object_name not in self.aimed_object_list:
            self.aimed_object_list.append(object_name)
            print(f"Added {object_name} to aimed objects list")
            self.update_state()

    def remove_aimed_object(self, object_name):
        if object_name in self.aimed_object_list:
            self.aimed_object_list.remove(object_name)
            print(f"Removed {object_name} from aimed objects list")
            self.update_state()

    def remove_all_aimed_objects(self):
        self.aimed_object_list.clear()
        print("Cleared all aimed objects from the list")
        self.update_state()

    def found_object_callback(self, sample: zenoh.Sample):
        self.remove_aimed_object(sample.payload.to_string())

    def destroy(self):
        self.sub.undeclare()
        self.session.close()

if __name__ == "__main__":
    forwarder = Forwarder()
    try:
        print("Started Forwarder Successfully")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        forwarder.destroy()
