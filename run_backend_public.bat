@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Virtual Sports Coach - Public Backend (Ngrok)
echo ===================================================

REM Ensure we are in the project root
if not exist "backend\main.py" (
    echo [ERROR] backend\main.py not found. Are you in the project root?
    pause
    exit /b 1
)

echo [1/2] Starting Ngrok Tunnel on port 8000...
start "Ngrok Tunnel" ngrok http 8000

echo.
echo [2/2] Starting Backend Server...
cd backend

REM --- VENV HANDLE ---
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM --- ACTIVATE ---
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)

echo [INFO] Installing dependencies (this may take a moment)...
python -m pip install -r requirements.txt >nul 2>&1

echo [INFO] Dependencies installed. Starting Uvicorn...
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
