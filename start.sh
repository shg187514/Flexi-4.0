#!/bin/bash
# Flexi Training System - Standalone Startup Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "=================================================="
echo " Starting Flexi Training Management System..."
echo "=================================================="

# 1. Check if application is already running on port 5001
if curl -s --max-time 1 "http://localhost:5001/" | grep -q "Vite + React"; then
    echo "Flexi Training System is already running on http://localhost:5001!"
    echo "Opening web browser..."
    (xdg-open "http://localhost:5001" || python3 -m webbrowser "http://localhost:5001") 2>/dev/null &
    exit 0
fi

# 2. Kill any stale process using port 5001 if not responding
fuser -k 5001/tcp 2>/dev/null || true
sleep 0.5

# 3. Find Python binary
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
    PYTHON_BIN="python"
else
    echo "Error: Python 3 is required to run this software."
    exit 1
fi

export OPEN_BROWSER=true
export PORT=5001

echo "Launching web browser and server on http://localhost:5001..."

# Background timer to ensure browser opens in Ubuntu desktop environment
(sleep 1.2 && (xdg-open "http://localhost:5001" || "$PYTHON_BIN" -m webbrowser "http://localhost:5001")) 2>/dev/null &

"$PYTHON_BIN" backend/app.py
