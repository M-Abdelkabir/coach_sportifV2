# Deployment Guide: Virtual Sports Coach

This guide provides instructions for deploying the Virtual Sports Coach application on both a local development machine (laptop) and a Raspberry Pi 5. The application consists of a FastAPI backend and a React frontend.

## 1. Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.9+** (for FastAPI backend)
*   **Node.js 18+** and **npm** or **yarn** (for React frontend)
*   **Git** (for cloning the repository)
*   **OpenCV** (for camera access and image processing, usually installed with `pip install opencv-python`)
*   **FFmpeg** (for video streaming, if not already present on your system)

### Raspberry Pi Specific Prerequisites

*   **Raspberry Pi OS (64-bit)** installed on your Raspberry Pi 5.
*   **GPIO Zero** and **RPi.GPIO** libraries for controlling LEDs and buzzer. These are typically pre-installed or can be installed via `pip`.
*   **Camera Module** connected and enabled on your Raspberry Pi.

## 2. Project Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd fitness-app
    ```

2.  **Create and activate a Python virtual environment for the backend:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install backend dependencies:**

    ```bash
    pip install -r backend/requirements.txt
    ```

4.  **Install frontend dependencies:**

    ```bash
    cd frontend
    npm install # or yarn install
    cd ..
    ```

## 3. Backend Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```env
DATABASE_URL="sqlite:///./sql_app.db"
# For Raspberry Pi, set to True to enable GPIO control
ENABLE_HARDWARE=False 
```

### Models

Ensure your `unified_model.pt`, `classifi_model_.pkl`, and `fitness_model.onnx` are located in the `backend/models/` directory.

## 4. Frontend Configuration

Create a `.env.local` file in the `frontend/` directory with the following variables:

```env
NEXT_PUBLIC_API_URL="http://localhost:8000"
NEXT_PUBLIC_WS_URL="ws://localhost:8000/ws"
```

*   If deploying on Raspberry Pi and accessing from another device, replace `localhost` with the Raspberry Pi's IP address.

## 5. Running the Application

### 5.1. On a Development Laptop

1.  **Start the backend (from the project root directory):**

    ```bash
    source venv/bin/activate
    uvicorn backend.main:app --reload
    ```

2.  **Start the frontend (from the `frontend/` directory):**

    ```bash
    npm run dev # or yarn dev
    ```

    The frontend will typically open in your browser at `http://localhost:3000`.

### 5.2. On Raspberry Pi 5

1.  **Enable Camera Interface:**

    ```bash
    sudo raspi-config
    # Navigate to Interface Options -> Camera -> Yes
    # Reboot if prompted
    ```

2.  **Install GStreamer (if not already installed, for better camera performance):**

    ```bash
    sudo apt update
    sudo apt install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x
    ```

3.  **Update `ENABLE_HARDWARE` in `backend/.env` to `True`:**

    ```env
    ENABLE_HARDWARE=True
    ```

4.  **Start the backend (from the project root directory):**

    ```bash
    source venv/bin/activate
    uvicorn backend.main:app --host 0.0.0.0 --port 8000
    ```

    *   Using `--host 0.0.0.0` makes the backend accessible from other devices on your network.

5.  **Start the frontend (from the `frontend/` directory):**

    ```bash
    npm run build
    npm start # or yarn start
    ```

    *   For a dedicated screen, you might configure the Raspberry Pi to auto-start the frontend in a kiosk mode browser on boot.

## 6. Hardware Connections (Raspberry Pi)

*   **RGB LED:**
    *   Red: GPIO 17
    *   Green: GPIO 27
    *   Blue: GPIO 22
*   **Buzzer:**
    *   GPIO 23

Ensure proper current limiting resistors are used for the LEDs to prevent damage to the Raspberry Pi.

## 7. Troubleshooting

*   **Camera not detected:** Check camera ribbon cable connection and ensure it's enabled in `raspi-config`.
*   **Backend not starting:** Verify Python environment, dependencies, and `uvicorn` command.
*   **Frontend not connecting:** Check `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` in `frontend/.env.local`.
*   **GPIO errors:** Ensure `ENABLE_HARDWARE=True` in `backend/.env` and `gpiozero`/`RPi.GPIO` are installed.

---

**Author:** Manus AI
**Date:** Feb 01, 2026
