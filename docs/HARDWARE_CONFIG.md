# Hardware & Camera Configuration

This guide details the wiring and physical configuration of your Virtual Sports Coach on Raspberry Pi 5.

## 1. GPIO Pinout
Here is the connection diagram for the Raspberry Pi pins:

| Component | GPIO Pin (BCM) | Type | Role |
| :--- | :--- | :--- | :--- |
| **Red LED** | GPIO 17 (Pin 11) | Output | Error / Incorrect Posture |
| **Green LED** | GPIO 27 (Pin 13) | Output | Success / Validated Rep |
| **Blue LED** | GPIO 22 (Pin 15) | Output | Initialization |
| **Buzzer** | GPIO 23 (Pin 16) | Output | Sound Signal |
| **Servo Pan** | GPIO 18 (Pin 12) | PWM | Camera Rotation (Auto-Centering) |
| **GND** | GND (Pin 6/9/14) | - | Common Ground |

## 2. Camera & Servo Installation
For auto-centering, the camera must be mounted on the servo motor.

### Physical Mounting
1. Attach the servo horn to the base of your camera mount.
2. Ensure camera cables have enough slack for a **180°** rotation (-90° to +90°).
3. Connect the servo control wire (usually Orange/Yellow) to **GPIO 18**.

### Camera Activation (Pi OS)
Launch the configuration tool:
```bash
sudo raspi-config
```
1. Go to **Interface Options**.
2. Select **Camera** and choose **Yes**.
3. Restart the Raspberry Pi.

## 3. Backend Optimization
To reduce latency on Raspberry Pi, install the GStreamer plugins:
```bash
sudo apt update
sudo apt install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools
```

## 4. Hardware Testing
You can use the diagnostic script to verify your wiring:
```bash
# In the backend/scripts/ folder
python test_hardware.py
```
*(If the script is not present, it will be available soon in the diagnostic tools.)*

---
**Author:** Moussaif Abdelkabir
**Date:** Feb 15, 2026