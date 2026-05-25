@echo off
title Tech Bytes Design — System Utility
cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

pip install -r requirements.txt -q --disable-pip-version-check 2>nul
python main.py %*
