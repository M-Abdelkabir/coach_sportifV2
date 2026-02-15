#!/bin/bash

# ==================================================================
# Virtual Sports Coach - Unified Setup & Run Script for Raspberry Pi
# ==================================================================

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

# 5. Hybrid Mode (Vercel + Pi) Setup
echo "-------------------------------------------------------"
echo "Would you like to configure for Hybrid Mode (Frontend on Vercel)?"
echo "This will install ngrok to expose your backend."
read -p "Configure Hybrid Mode? [y/N]: " hybrid_choice

if [[ "$hybrid_choice" =~ ^[Yy]$ ]]; then
    echo "Checking for ngrok..."
    if ! command -v ngrok &> /dev/null; then
        echo "Installing ngrok..."
        curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
        echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
        sudo apt-get update && sudo apt-get install -y ngrok
        echo "Ngrok installed."
    else
        echo "Ngrok already installed."
    fi

    echo "-------------------------------------------------------"
    echo "To link with Vercel, you need a free ngrok account."
    echo "If you have an authtoken, enter it now (or press Enter to skip):"
    read -p "Ngrok Authtoken: " authtoken
    if [ ! -z "$authtoken" ]; then
        ngrok config add-authtoken $authtoken
    fi
    
    # Update frontend .env.local for Vercel reference (even if built locally)
    echo "Note: For Vercel, you will need to start ngrok first to get the URL."
    echo "The .env.local will be updated with a placeholder for now."
fi

# 6. Summary
echo "-------------------------------------------------------"
echo "[OK] Setup Complete!"
echo "-------------------------------------------------------"

# 7. Execution Menu
echo "How would you like to run the application?"
echo "1) Standard Mode (Pi Only - Local Network)"
echo "2) Hybrid Mode (Expose Backend via Ngrok)"
echo "3) Background Mode (Screen - Standard)"
echo "4) Exit"
read -p "Selection [1-4]: " choice

case $choice in
    1)
        echo "Starting standard mode..."
        source venv/bin/activate && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
        ;;
    2)
        echo "Starting Hybrid Mode..."
        echo "1. Launching Ngrok tunnel..."
        screen -dmS ngrok bash -c "ngrok http 8000"
        sleep 3
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*ngrok-free.app' | head -n 1)
        
        if [ -z "$NGROK_URL" ]; then
            echo "[ERROR] Could not get Ngrok URL. Is ngrok configured with an authtoken?"
            echo "Try running 'ngrok http 8000' manually to debug."
        else
            echo "-------------------------------------------------------"
            echo "LINK TO VERCEL:"
            echo "API URL: $NGROK_URL"
            echo "WS URL: ${NGROK_URL/https/wss}/ws"
            echo "-------------------------------------------------------"
            echo "Use these values in your Vercel Environment Variables."
        fi
        
        echo "Starting backend..."
        source venv/bin/activate && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
        ;;
    3)
        echo "Starting in background screens: 'backend' and 'frontend'..."
        screen -dmS backend bash -c "source venv/bin/activate && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000"
        screen -dmS frontend bash -c "cd frontend && npm start"
        echo "Done! Use 'screen -r backend' to view logs."
        ;;
    *)
        echo "Exiting."
        ;;
esac
