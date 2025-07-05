@echo off
setlocal

rem Default Python path
set "PY_EXE=C:\Program Files\ANSYS Inc\v251\AnsysEM\commonfiles\CPython\3_10\winx64\Release\python\python.exe"

:CHECK_EXIST
if exist "%PY_EXE%" (
    goto CHECK_VERSION
) else (
    echo Python not found at:
    echo    %PY_EXE%
    set /P PY_EXE=Enter path to python.exe (or Ctrl+C to cancel): 
    if not exist "%PY_EXE%" (
        echo Path "%PY_EXE%" does not exist.
        goto CHECK_EXIST
    )
)

:CHECK_VERSION
for /f "tokens=1,2 delims=." %%A in ('"%PY_EXE%" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do (
    set "PMAJOR=%%A"
    set "PMINOR=%%B"
)
if %PMAJOR% LSS 3 (
    goto VERSION_WARN
)
if %PMAJOR%==3 if %PMINOR% LSS 10 (
    goto VERSION_WARN
)

:CREATE_VENV
echo Using %PY_EXE%
"%PY_EXE%" -m venv venv
if errorlevel 1 (
    echo Failed to create virtual environment.
    exit /b 1
)

echo Installing required modules...
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt

echo Virtual environment setup complete.
pause
exit /b 0

:VERSION_WARN
echo Detected Python version %PMAJOR%.%PMINOR%.
echo Python 3.10 or higher is required.
choice /M "Provide a different path?"
if errorlevel 2 (
    echo Installation aborted.
    exit /b 1
) else (
    set /P PY_EXE=Enter path to python.exe (or Ctrl+C to cancel): 
    goto CHECK_EXIST
)
