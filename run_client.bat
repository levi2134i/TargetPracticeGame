@echo off
set /p IP="Enter Server IP (default: localhost): "
if "%IP%"==" " set IP=localhost
echo Connecting to %IP%...
python client.py %IP%
pause
