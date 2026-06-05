## How to use

In order to use this app you must
 - SSH on the raspberry pi, then cd to src/ and run
 ```bash
 bash ./launch/pi.bash
 ```
 - On your computer, run in one terminal
 ```bash
cd ./src/
python ./video/detect_objects.py
 ```
 And in another terminal
 ```bash
python ./website/app.py
 ```

This will launch the webapp in https://localhost::8000
