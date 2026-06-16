@echo off
cd /d "%~dp0"
echo Starting RiseStore Desktop app...
if not exist "desktop\venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv desktop\venv
    echo Installing dependencies...
    desktop\venv\Scripts\pip install -r desktop\requirements.txt
)
desktop\venv\Scripts\python desktop\main.py
pause
