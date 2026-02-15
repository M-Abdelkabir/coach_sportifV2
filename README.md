# Virtual Sports Coach - Complete Documentation

Welcome to the **Virtual Sports Coach** project. This document explains in detail how the system works, its architecture, its features, and the necessary prerequisites.

---

## Project Architecture

The project follows a modern **Client-Server** architecture with a clear separation between data processing (Backend) and the user interface (Frontend).

### 1. Global Structure
- **Backend**: FastAPI server (Python) that handles camera capture, processes real-time data streams, and exposes an MJPEG video stream.
- **Frontend**: React/Next.js application that displays the interface, receives the video stream from the backend, and shows user feedback.
- **ML Models**: Artificial Intelligence engines for pose detection and exercise classification.

### 2. Data Flow (Real-time)
1. The **Backend** captures images directly from the camera (via OpenCV).
2. The **Backend** processes each image with **MediaPipe** to extract 33 key points.
3. The **LSTM** and **ONNX** models analyze these points to validate posture.
4. The **Backend** sends results (repetitions, errors, confidence) via **WebSockets**.
5. Simultaneously, the **Backend** broadcasts the processed video stream (with skeleton) via an HTTP endpoint (`/video_feed`).
6. The **Frontend** receives the video stream and displays dynamic feedback.

---

## Core Features

### 1. Real-Time Pose Analysis
Using **MediaPipe** and **YOLOv11-Pose** to track body movements with millimeter precision, even on low-power machines (like the Raspberry Pi).

### 2. Intelligent Classification (LSTM)
A recurrent neural network model (LSTM) analyzes movement sequences to precisely identify the exercise being performed (Squat, Pushup) and its quality.

### 3. Comfort Features
- **Camera Auto-Centering**: Uses a servo motor to automatically orient the camera and keep the user in the center of the frame.
- **Voice Feedback**: Uses the **Web Speech API** to provide tips (e.g., "Keep your back straight!") without the user needing to look at the screen.

### 4. Performance Tracking
- **Repetition Counter**: Automatic detection of up and down phases.
- **History**: Session saving in a **SQLite** database.
- **Statistics**: Progress visualization via a dashboard.

### 5. Hybrid Mode (Pi + PC)
Ability to run the backend on a Raspberry Pi and the frontend on a PC, or everything on the same machine.

---

## Technical Requirements

### Software
- **Python 3.9+**: For the calculation engine and AI.
- **Node.js 18+**: For the user interface.
- **Key Libraries**:
  - `mediapipe`: Skeleton detection.
  - `fastapi`: High-performance web server.
  - `ultralytics` (YOLO): Alternative for pose.
  - `tensorflow/keras`: For the LSTM model.

### Hardware
- **Webcam**: 720p recommended for better detection.
- **Processor**: Modern CPU (Intel i5/Ryzen 5) or Raspberry Pi 4/5.
- **Memory**: Minimum 4 GB of RAM.

---

## Installation & Usage

### 1. Backend Preparation
```bash
cd backend
python -m venv venv
# Activate the venv (Windows: venv\Scripts\activate)
pip install -r requirements.txt
python main.py
```

### 2. Frontend Preparation
```bash
cd frontend
npm install
npm run dev
```

Access `http://localhost:3000` to start your training.

---

## Folder Structure (After Cleanup)
- `/backend/tests`: Model validation tests.
- `/backend/models`: AI models (.h5, .onnx, .pt, .task).
- `/backend/scripts`: Installation and launch scripts.
- `/frontend/components`: UI components (React).
- `/docs`: Detailed guides and architecture.

---

### 📄 Complete Documentation
For more details, see the specific guides:
- [Hybrid Deployment Guide (Vercel + Pi)](docs/DEPLOYMENT_VERCEL_PI.md)
- [Hardware Configuration (LEDs, Buzzer, Servo)](docs/HARDWARE_CONFIG.md)
- [Raspberry Pi Installation Guide](docs/Setup_RaspberryPi.md)
- [System Architecture](docs/Architecture.md)

---

*Developed to provide an intelligent and accessible sports coaching experience.*
 
---
**Author:** Moussaif Abdelkabir
**Date:** Feb 15, 2026