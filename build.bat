@echo off
cd /d "%~dp0"

echo ================================================
echo   Building RiseStore Desktop - Single Binary
echo ================================================

if not exist "desktop\venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv desktop\venv
)
echo Activating virtual environment...
call desktop\venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r desktop\requirements.txt

python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo Building binary...
python -m PyInstaller --onefile ^
    --windowed ^
    --name "RiseStore" ^
    --add-data "desktop\fonts;desktop\fonts" ^
    --hidden-import desktop.db ^
    --hidden-import desktop.app ^
    --hidden-import desktop.utils ^
    --hidden-import desktop.fonts ^
    --hidden-import desktop.views.login ^
    --hidden-import desktop.views.dashboard ^
    --hidden-import desktop.views.customers ^
    --hidden-import desktop.views.products ^
    --hidden-import desktop.views.sales ^
    --hidden-import desktop.views.payments ^
    --hidden-import desktop.views.reports ^
    --hidden-import jdatetime ^
    --hidden-import tkinter ^
    --hidden-import sqlite3 ^
    --distpath dist ^
    --workpath build_tmp ^
    desktop\main.py

echo.
echo ================================================
echo   Build complete!
echo   Binary: dist\RiseStore.exe
echo ================================================
pause
