@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Virtual Sports Coach - Setup & Run Script
echo ===================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    pause
    exit /b 1
)

echo [INFO] Environment checks passed.
echo.

REM --- BACKEND STARTUP ---
echo [1/2] Launching Backend...
echo     - Creating/Activating venv
echo     - Installing dependencies
echo     - Starting FastAPI server
start "Virtual Sports Coach - Backend" cmd /k "cd backend/scripts && call run_backend.bat"

REM --- FRONTEND STARTUP ---
echo.
echo [2/2] Launching Frontend...
echo     - Installing dependencies
echo     - Starting Next.js dev server
start "Virtual Sports Coach - Frontend" cmd /k "cd frontend && echo Installing dependencies... && npm install && echo Starting frontend... && npm run dev"

echo.
echo ===================================================
echo   Full System Startup Initiated!
echo.
echo   [Backend]  http://127.0.0.1:8000
echo   [Frontend] http://localhost:3000
echo.
echo   Please wait a few moments for the servers to be ready.
echo ===================================================
echo.
pause
