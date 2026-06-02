supposed to run on the pi :

zdrive
aim
capture_video (-a picamera)
    python3 video/capture_video.py -a picamera -e tcp/YOUR_ZENOH_IP:7447

on ur pc
detect_objects
forwarder


to display the pi camera
python .\display_video.py -l tcp/0.0.0.0:7447