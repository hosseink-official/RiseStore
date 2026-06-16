#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting RiseStore Desktop app..."
cd "$ROOT_DIR"
source desktop/venv/bin/activate
python desktop/main.py
