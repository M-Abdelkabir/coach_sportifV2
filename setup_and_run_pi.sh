#!/bin/bash

# =================================================================
# Virtual Sports Coach - Unified Setup & Run Script for Raspberry Pi
# =================================================================

set -e # Exit on error

echo "-------------------------------------------------------"
echo "  Virtual Sports Coach - Raspberry Pi Deployment"
echo "-------------------------------------------------------"

# 1. System Dependencies
echo "[1/5] Checking System Dependencies..."
sudo apt-get update
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libatlas-base-dev \
                        nodejs npm screen xdg-utils

# 2. Backend Setup
echo "[2/5] Setting up Backend..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install gpiozero RPi.GPIO lgpio

# Handle Backend .env
if [ ! -f "backend/.env" ]; then
    echo "Creating default backend/.env..."
    echo 'DATABASE_URL="sqlite:///./coach.db"' > backend/.env
    echo 'ENABLE_HARDWARE=True' >> backend/.env
fi

# 3. Frontend Setup
echo "[3/5] Setting up Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

# Handle Frontend .env.local
if [ ! -f ".env.local" ]; then
    PI_IP=$(hostname -I | awk '{print $1}')
    echo "Creating frontend/.env.local with IP: $PI_IP..."
    echo "NEXT_PUBLIC_API_URL=\"http://$PI_IP:8000\"" > .env.local
    echo "NEXT_PUBLIC_WS_URL=\"ws://$PI_IP:8000/ws\"" >> .env.local
fi

# Build for production
echo "Building frontend (this may take a few minutes on Pi)..."
npm run build
cd ..

# 4. Summary
echo "-------------------------------------------------------"
echo "[OK] Setup Complete!"
echo "-------------------------------------------------------"

# 5. Execution Menu
echo "How would you like to run the application?"
echo "1) Run in background (Screen)"
echo "2) Run in foreground (Stop with Ctrl+C)"
echo "3) Exit"
read -p "Selection [1-3]: " choice

case $choice in
    1)
        echo "Starting in background screens: 'backend' and 'frontend'..."
        screen -dmS backend bash -c "source venv/bin/activate && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000"
        screen -dmS frontend bash -c "cd frontend && npm start"
        echo "Done! Use 'screen -r backend' or 'screen -r frontend' to view logs."
        ;;
    2)
        echo "Starting in foreground..."
        echo "Note: This will only start the backend here. Open another terminal for frontend."
        source venv/bin/activate && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
        ;;
    *)
        echo "Exiting. You can run manually later."
        ;;
esac
