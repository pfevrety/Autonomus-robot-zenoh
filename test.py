import zenoh
import json
import time

conf = zenoh.Config()
session = zenoh.open(conf)
searched_object = "banana"
for i in range(30):
    sample = json.dumps(
        {
            "name": "banana",
            "confiance": int(99),
            "box": [100, 150, 200, 250],
            "normalized_box": [0.1, 0.15, 0.2, 0.25],
            "raw_center": [150, 200],
            "center": [150, 200],
            "normalized_center": [
                (100 + i) / 200,
                200 / 250,
            ],
        }
    )
    session.put("robot/aimed", sample)
    time.sleep(0.1)
