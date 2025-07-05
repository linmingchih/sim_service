@echo off
set PORT=5000
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4 Address"') do (
    set IP=%%A
    goto :gotip
)
:gotip
set IP=%IP:~1%
echo Server will be available at http://%IP%:%PORT%
python flask_app.py
