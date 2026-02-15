#!/bin/bash
# Setup script for Raspberry Pi 5

# Change directory to the backend root
cd "$(dirname "$0")/.."

echo "[PI-SETUP] Starting Virtual Sports Coach setup for Raspberry Pi in $(pwd)..."

# Update system
sudo apt-get update
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libatlas-base-dev

# Install GPIO libraries
echo "[PI-SETUP] Installing GPIO and Hardware libraries..."
pip install gpiozero RPi.GPIO lgpio

# Install project dependencies
echo "[PI-SETUP] Installing project dependencies..."
pip install -r requirements.txt

# Create models directory if not exists
mkdir -p models

echo "[PI-SETUP] Setup complete! You can now run the project with: python main.py"
echo "Note: If using real sensors (MAX30102, MPU6050), ensure they are connected to I2C pins."
