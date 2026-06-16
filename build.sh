#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "================================================"
echo "  Building RiseStore Desktop - Single Binary"
echo "================================================"

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

VENV_DIR="$ROOT_DIR/desktop/venv"
if [ -f "$VENV_DIR/bin/activate" ]; then
    echo "Activating existing virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
fi

echo "Installing dependencies..."
pip install -r desktop/requirements.txt

if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

echo "Building binary..."
python -m PyInstaller --onefile \
    --windowed \
    --name "RiseStore" \
    --add-data "desktop/fonts:desktop/fonts" \
    --hidden-import desktop.db \
    --hidden-import desktop.app \
    --hidden-import desktop.utils \
    --hidden-import desktop.fonts \
    --hidden-import desktop.views.login \
    --hidden-import desktop.views.dashboard \
    --hidden-import desktop.views.customers \
    --hidden-import desktop.views.products \
    --hidden-import desktop.views.sales \
    --hidden-import desktop.views.payments \
    --hidden-import desktop.views.reports \
    --hidden-import jdatetime \
    --hidden-import tkinter \
    --hidden-import sqlite3 \
    --distpath dist \
    --workpath build_tmp \
    desktop/main.py

echo ""
echo "================================================"
echo "  Build complete!"
echo "  Binary: dist/RiseStore"
echo "================================================"
