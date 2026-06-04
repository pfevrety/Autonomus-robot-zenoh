@echo off
echo Launching all computer run files

echo Starting detect_objects.py...
start /b python -u ./video/detect_objects.py

:: echo Starting forwarder.py...
:: start /b python -u ./video/forwarder.py

:: echo Starting aim.py...
:: start /b python -u ./control/aim.py

echo Everything started successfully
echo Don't forget to start the zenoh router.
echo Press Ctrl+C to stop all processes.

:loop
timeout /t 1 /nobreak >nul 2>&1
goto loop

:cleanup
echo Stopping all Python processes...
wmic process where "commandline like '%detect_objects.py%'" delete
:: wmic process where "commandline like '%aim.py%'" delete
:: wmic process where "commandline like '%forwarder.py%'" delete
exit /b