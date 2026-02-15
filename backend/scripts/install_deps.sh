#!/bin/bash
# Install backend dependencies for Virtual Sports Coach

# Change directory to the backend root
cd "$(dirname "$0")/.."

echo "Installing Python dependencies in $(pwd)..."
sudo pip3 install fastapi uvicorn mediapipe opencv-python numpy aiosqlite pydantic ultralytics onnxruntime pyttsx3 scikit-learn

echo "Installing system dependencies for Raspberry Pi (if applicable)..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y libatlas-base-dev libportaudio2
fi

echo "Dependencies installed successfully!"
