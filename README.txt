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

to launch the pin camera at low quality
 python3 video/capture_video.py -a picamera -e tcp/10.126.190.52:7447 -w 512 -q 70