@echo off
setlocal enabledelayedexpansion

echo [BACKEND] Starting Virtual Sports Coach Backend...
echo.

REM --- VENV CHECK ---
if not exist venv goto :create_venv

echo [BACKEND] Checking virtual environment integrity...
venv\Scripts\python -V >nul 2>&1
if !errorlevel! equ 0 goto :venv_healthy

echo [BACKEND] WARNING: Virtual environment seems broken.
echo [BACKEND] Removing broken environment...
rmdir /s /q venv

:create_venv
echo [BACKEND] Creating new virtual environment...
python -m venv venv
if !errorlevel! neq 0 (
    echo [BACKEND] ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

:venv_healthy
echo [BACKEND] Virtual environment is available.

REM --- ACTIVATION ---
call venv\Scripts\activate
if !errorlevel! neq 0 (
    echo [BACKEND] ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM --- DEPENDENCIES ---
echo [BACKEND] Checking dependencies...
python -m pip install --upgrade pip
python -m pip install --retries 10 --default-timeout=1000 -r requirements.txt
if !errorlevel! neq 0 (
    echo [BACKEND] ERROR: Failed to install dependencies despite retries.
    echo [BACKEND] Please check your connection and try running the script again.
    pause
    exit /b 1
)

REM --- RUN SERVER ---
echo [BACKEND] Launching application...
echo.
REM Use uvicorn directly to exclude venv from reload watch (avoids infinite loops with pyttsx3)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude venv --log-level info

if !errorlevel! neq 0 (
    echo [BACKEND] Server stopped with error code !errorlevel!.
    pause
)
