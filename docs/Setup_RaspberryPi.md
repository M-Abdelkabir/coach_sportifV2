# Installation Guide: Virtual Sports Coach on Raspberry Pi

This guide walks you through the installation and launch of the project on a Raspberry Pi 5.

## 1. Automated Installation (Recommended)
We have created an all-in-one script to simplify installation.

```bash
# Make the script executable
chmod +x setup_and_run_pi.sh

# Launch installation and startup
./setup_and_run_pi.sh
```
This script will take care of installing system dependencies, configuring virtual environments, and building the frontend.

## 2. Required Hardware
- Raspberry Pi 5 (8GB recommended).
- USB Camera or RPi Camera Module (v2 or v3).
- RGB LED and Buzzer (Optional, for physical feedback).
- SSD or MicroSD Card (64GB+).

## 3. System Preparation
Make sure to use **Raspberry Pi OS (64-bit)**.

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies for OpenCV and MediaPipe
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libatlas-base-dev
```

## 4. Project Installation
Clone the project and configure the Python environment.

```bash
# Navigate to the project folder
cd virtual-sports-coach-final

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
pip install gpiozero RPi.GPIO lgpio
```

## 5. Configuration
### Backend
Create a `backend/.env` file:
```env
DATABASE_URL="sqlite:///./coach.db"
ENABLE_HARDWARE=True
```

### Frontend
Create a `frontend/.env.local` file:
```env
# Replace <IP_DU_PI> with your Raspberry Pi's actual IP address
NEXT_PUBLIC_API_URL="http://<PI_IP>:8000"
NEXT_PUBLIC_WS_URL="ws://<PI_IP>:8000/ws"
```

## 6. Launching
It is recommended to open two terminals.

### Terminal 1: Backend
```bash
source venv/bin/activate
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm install
npm run build
npm start
```

## 7. Hybrid Configuration (PC + Raspberry Pi)
If you want to run the **Frontend on your PC** and the **Backend on the Pi**:

1. **On the Raspberry Pi**:
   - Start the backend as shown in step 6 with `--host 0.0.0.0`.
   - Note the Pi's IP address (type `hostname -I` in the terminal).

2. **On your PC**:
   - Go to the `frontend` folder.
   - Modify (or create) the `.env.local` file.
   - Replace `localhost` with the Pi's IP address:
     ```env
     NEXT_PUBLIC_API_URL="http://192.168.x.x:8000"
     NEXT_PUBLIC_WS_URL="ws://192.168.x.x:8000/ws"
     ```
   - Launch the frontend: `npm run dev`.

## 8. Hardware Wiring (GPIO)
If you are using physical components:
- **Red LED**: GPIO 17
- **Green LED**: GPIO 27
- **Blue LED**: GPIO 22
- **Buzzer**: GPIO 23
- **Servo Pan**: GPIO 18
- **GND**: Any Ground pin (e.g., Pin 6).

## 9. Kiosk Mode (Optional)
To turn the Pi into a dedicated station, launch Chromium on startup:
```bash
chromium-browser --kiosk http://localhost:3000
```

---
**Author:** Moussaif Abdelkabir
**Date:** Feb 15, 2026