@echo off
echo Launching all computer run files

echo Starting detect_objects.py...
start /b python -u ./video/detect_objects.py

echo Starting forwarder.py...
start /b python -u ./video/forwarder.py

echo Starting aim.py...
start /b python -u ./control/aim.py

echo Everything started successfully
echo Don't forget to start the zenoh router.

:: This keeps the CMD window open so you can see the logs
pause