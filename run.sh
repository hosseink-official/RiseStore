#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting RiseStore Desktop app..."
cd "$ROOT_DIR"
if [ -f desktop/venv/bin/activate ]; then
    source desktop/venv/bin/activate
fi
python desktop/main.py
