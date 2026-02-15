# Automated Hybrid Deployment: Vercel (Frontend) + Raspberry Pi (Backend)

This guide explains how to use the automated script to link your frontend on Vercel with your backend on Raspberry Pi.

## 1. Using the Automated Script
We have simplified the process. You no longer need to install ngrok manually.

1. On your Raspberry Pi, run the root script:
   ```bash
   chmod +x setup_and_run_pi.sh
   ./setup_and_run_pi.sh
   ```
2. When the script asks **"Configure Hybrid Mode?"**, answer **"y"**.
3. If you have a free ngrok account (recommended), enter your **authtoken** when prompted.

## 2. Launching the tunnel and retrieving URLs
Once the installation is complete, use the startup menu:
1. Choose **Option 2) Hybrid Mode (Expose Backend via Ngrok)**.
2. The script will create the tunnel and display the URLs to use directly:
   ```text
   LINK TO VERCEL:
   API URL: https://xyz.ngrok-free.app
   WS URL: wss://xyz.ngrok-free.app/ws
   ```

## 3. Configuration on Vercel
1. Go to your **Vercel** dashboard.
2. In your project settings (**Environment Variables**), add:
   - `NEXT_PUBLIC_API_URL`: The URL displayed by the script (e.g., `https://xyz.ngrok-free.app`)
   - `NEXT_PUBLIC_WS_URL`: The WebSocket URL displayed by the script (e.g., `wss://xyz.ngrok-free.app/ws`)
3. Deploy or redeploy your frontend.

> [!IMPORTANT]
> The ngrok URL changes every time you restart the script (unless you have a paid account with a fixed domain). Remember to update the variables on Vercel if necessary.

## 4. Security and CORS
The backend allows all origins by default in development mode, but for more security in `backend/main.py`, you can restrict to Vercel domains:
```python
origins = [
    "https://your-project.vercel.app",
    "*" # Allowed by default to simplify initial setup
]
```

---
**Author:** Moussaif Abdelkabir
**Date:** Feb 15, 2026