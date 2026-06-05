import zenoh
import json
import time

conf = zenoh.Config()
session = zenoh.open(conf)
searched_object = "banana"
session.put("robot/found_object", searched_object.encode())
