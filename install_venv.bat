@echo off
setlocal

REM Candidate python paths in priority order
set "PY1=C:\Program Files\ANSYS Inc\v251\AnsysEM\commonfiles\CPython\3_10\winx64\Release\python\python.exe"
set "PY2=C:\Program Files\AnsysEM\v242\Win64\commonfiles\CPython\3_10\winx64\Release\python\python.exe"
set "PY3=C:\Program Files\AnsysEM\v241\Win64\commonfiles\CPython\3_10\winx64\Release\python\python.exe"
set "PY4=C:\Program Files\AnsysEM\v232\Win64\commonfiles\CPython\3_10\winx64\Release\python\python.exe"

set "PY_EXE="
if exist "%PY1%" set "PY_EXE=%PY1%"
if not defined PY_EXE if exist "%PY2%" set "PY_EXE=%PY2%"
if not defined PY_EXE if exist "%PY3%" set "PY_EXE=%PY3%"
if not defined PY_EXE if exist "%PY4%" set "PY_EXE=%PY4%"

if not defined PY_EXE (
    echo Python not found in default locations.
    set /P "PY_EXE=Enter full path to python.exe (or Ctrl+C to cancel): "
)

:CheckPath
if not exist "%PY_EXE%" (
    echo Python not found at %PY_EXE%
    set /P "PY_EXE=Enter full path to python.exe (or Ctrl+C to cancel): "
    goto CheckPath
)

REM Query python version into temp file
"%PY_EXE%" -c "import sys; sys.stdout.write(str(sys.version_info.major)+'.'+str(sys.version_info.minor))" > pyver.tmp 2>nul
if not exist pyver.tmp (
    echo Unable to run python version check.
    pause
    exit /b 1
)

for /f "tokens=1,2 delims=." %%A in (pyver.tmp) do (
    set "PMAJOR=%%A"
    set "PMINOR=%%B"
)
del pyver.tmp

if "%PMAJOR%"=="" (
    echo Unable to detect Python version.
    pause
    exit /b 1
)

if %PMAJOR% LSS 3 goto VersionWarn
if %PMAJOR% EQU 3 if %PMINOR% LSS 10 goto VersionWarn

:CreateVenv
echo Using "%PY_EXE%"
"%PY_EXE%" -m venv venv || (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

echo Installing packages...
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt || (
    echo Package installation failed.
    pause
    exit /b 1
)

echo Virtual environment setup complete.
pause
exit /b 0

:VersionWarn
echo Detected Python version %PMAJOR%.%PMINOR%. Python 3.10 or higher is required.
set /P "RETRY=Provide different python.exe path? (Y/N): "
if /I "%RETRY%"=="Y" (
    set /P "PY_EXE=Enter full path to python.exe: "
    goto CheckPath
)
exit /b 1
