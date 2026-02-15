# Deployment Guide: Virtual Sports Coach

This guide provides instructions for deploying the Virtual Sports Coach application on both a local development machine (laptop) and a Raspberry Pi 5. The application consists of a FastAPI backend and a React frontend.

## 1. Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.9+** (for FastAPI backend)
*   **Node.js 18+** and **npm** or **yarn** (for React frontend)
*   **Git** (for cloning the repository)
*   **OpenCV** (for camera access and image processing)
*   **FFmpeg** (for video streaming support)

### Raspberry Pi Specific Prerequisites

*   **Raspberry Pi OS (64-bit)** installed on your Raspberry Pi 5.
*   **GPIO Zero** and **RPi.GPIO** libraries for hardware control.
*   **Camera Module** connected and enabled.

## 2. Project Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd fitness-app
    ```

2.  **Create and activate a Python virtual environment:**
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
    npm install
    cd ..
    ```

## 3. Backend Configuration

### Environment Variables
Create a `.env` file in the `backend/` directory:
```env
DATABASE_URL="sqlite:///./sql_app.db"
ENABLE_HARDWARE=False # Set to True for Raspberry Pi
```

## 4. Frontend Configuration
Create a `.env.local` file in the `frontend/` directory:
```env
NEXT_PUBLIC_API_URL="http://localhost:8000"
NEXT_PUBLIC_WS_URL="ws://localhost:8000/ws"
```
*Replace `localhost` with your Raspberry Pi's IP if accessing remotely.*

## 5. Running the Application

### 5.1 On a Development Laptop
1. **Backend**: `uvicorn backend.main:app --reload`
2. **Frontend**: `npm run dev`

### 5.2 On Raspberry Pi 5
1. **Enable Camera**: `sudo raspi-config` -> Interface Options -> Camera -> Yes.
2. **Set `ENABLE_HARDWARE=True`** in `backend/.env`.
3. **Backend**: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
4. **Frontend**: `npm run build && npm start`

## 6. Hardware Connections
See [Hardware Configuration](HARDWARE_CONFIG.md) for detailed wiring diagrams.

---
**Author:** Moussaif Abdelkabir
**Date:** Feb 15, 2026