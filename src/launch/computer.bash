#!/bin/bash

echo "Launching all computer run files"

echo "Starting detect_objects.py..."
python -u ./video/detect_objects.py &

echo "Starting forwarder.py..."
python -u ./video/forwarder.py &

echo "Starting aim.py..."
python -u ./control/aim.py &

echo "Everything started successfully"
echo "Don't forget to start the zenoh router."

wait