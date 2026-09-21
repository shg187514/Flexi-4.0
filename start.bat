@echo off
title Flexi Training Management System
cd /d "%~dp0"

echo ==================================================
echo  Starting Flexi Training Management System...
echo ==================================================

if exist ".venv\Scripts\python.exe" (
    set PYTHON_BIN=".venv\Scripts\python.exe"
) else (
    set PYTHON_BIN=python
)

set OPEN_BROWSER=true
set PORT=5001

echo Opening web browser to http://localhost:5001...
start "" "http://localhost:5001"

echo Launching server background process...
%PYTHON_BIN% backend\app.py
pause
