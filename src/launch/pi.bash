#!/bin/bash
echo "Launching all scripts ran by the pi"

# Terminate all background processes if the script is interrupted (Ctrl+C)
trap 'kill $(jobs -p) 2>/dev/null' EXIT

# 1. Check if the first argument ($1) is provided
# -z checks if the string is empty
if [ -z "$1" ]; then
    echo "Error: No IP address provided."
    echo "Usage: $0 <GIVEN_IP>"
    exit 1
fi

GIVEN_IP=$1

echo "Starting capture video.py..."
python3 video/capture_video.py -a picamera -e tcp/$GIVEN_IP:7447 -w 512 -q 70 &

echo "Starting zdrive.py"
python ./motor/zdrive.py &

echo "Starting aim.py"
python ./motor/aim.py &

echo "Everything started succesfully"
echo "Don't forget to start the zenoh router."

wait

