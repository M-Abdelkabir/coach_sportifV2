@echo off
REM Virtual Sports Coach - Windows Dependency Installer

REM Change directory to the backend root
cd /d "%~dp0.."

echo ========================================
echo Virtual Sports Coach - Dependency Setup
echo ========================================
echo.

REM Check if Python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH!
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)
python -m venv venv
venv\Scripts\activate

echo Step 1: Installing Python dependencies...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)

python -m pip install fastapi uvicorn mediapipe opencv-python numpy aiosqlite pydantic ultralytics onnxruntime pyttsx3 scikit-learn
if %errorlevel% neq 0 (
    echo ERROR: Failed to install some packages
    echo You may need to install Microsoft Visual C++ Build Tools
    pause
    exit /b 1
)

echo.
echo Step 2: Windows-specific setup notes...
echo.
echo IMPORTANT: Some features may require additional setup:
echo 1. For optimal performance, install Microsoft Visual C++ Redistributable
echo 2. For audio features, you may need to install pyaudio: python -m pip install pyaudio
echo 3. Ensure your Windows is up to date for best mediapipe performance
echo.

echo ========================================
echo Setup completed successfully!
echo ========================================
pause