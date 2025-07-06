@echo off

if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found.
    echo Please run install_venv.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate

set PORT=5000

for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R "IPv4 Address"') do (
    set "rawip=%%A"
    goto :parse_ip
)

:parse_ip
set "IP=!rawip:~1!"

echo Server will be available at http://!IP!:%PORT%

python service\flask_app.py
