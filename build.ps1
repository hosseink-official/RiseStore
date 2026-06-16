$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

Write-Host "================================================"
Write-Host "  Building RiseStore Desktop - Single Binary"
Write-Host "================================================"

$venvDir = Join-Path $rootDir "desktop\venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venvDir
}

Write-Host "Activating virtual environment..."
. "$venvDir\Scripts\Activate.ps1"

Write-Host "Installing dependencies..."
pip install -r desktop\requirements.txt

try {
    $null = python -c "import PyInstaller"
} catch {
    Write-Host "Installing PyInstaller..."
    pip install pyinstaller
}

Write-Host "Building binary..."
python -m PyInstaller --onefile `
    --windowed `
    --name "RiseStore" `
    --add-data "desktop\fonts;desktop\fonts" `
    --hidden-import desktop.db `
    --hidden-import desktop.app `
    --hidden-import desktop.utils `
    --hidden-import desktop.fonts `
    --hidden-import desktop.views.login `
    --hidden-import desktop.views.dashboard `
    --hidden-import desktop.views.customers `
    --hidden-import desktop.views.products `
    --hidden-import desktop.views.sales `
    --hidden-import desktop.views.payments `
    --hidden-import desktop.views.reports `
    --hidden-import jdatetime `
    --hidden-import tkinter `
    --hidden-import sqlite3 `
    --distpath dist `
    --workpath build_tmp `
    desktop\main.py

Write-Host "`n================================================"
Write-Host "  Build complete!"
Write-Host "  Binary: dist\RiseStore.exe"
Write-Host "================================================"
Read-Host "Press Enter to exit"
