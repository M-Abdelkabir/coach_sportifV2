"""
FastAPI Backend for Virtual Sports Coach.
Main application with REST endpoints and WebSocket for real-time pose streaming.
"""
import asyncio
import json
import time
import os
import cv2  # Added for video streaming
import io   # Added for BytesIO
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
import numpy as np
from functools import lru_cache

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

# Local imports
import database as db
from models import (
    UserCreate, UserProfile, UserUpdate,
    CalibrationRequest, CalibrationResult,
    SessionData, SessionSummary,
    WSMessage, WSMessageType,
    HealthCheck, APIResponse
)
# from pose_detector import get_pose_detector, PoseDetector, POSE_LANDMARKS # Original import
from pose_detector import PoseDetector, POSE_LANDMARKS # Import PoseDetector and POSE_LANDMARKS directly
from exercise_engine import get_exercise_engine, ExerciseType, map_exercise_name, lstm_model
from calibration import Calibrator, CalibrationConfig, run_calibration_async, get_calibrator
from feedback import get_feedback_engine, POSTURE_MESSAGES
from hardware_manager import get_hardware_manager


@lru_cache()
def get_pose_detector() -> PoseDetector:
    """Cached function to get the pose detector instance."""
    # This function is now defined locally to allow modification of its parameters
    return PoseDetector() 


# ==================== App Lifecycle ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    print("[STARTUP] Initializing systems...")
    # Initialize database first
    await db.init_db()
    # Preload singletons
    get_pose_detector()
    get_exercise_engine()
    get_calibrator()
    get_feedback_engine()
    get_hardware_manager()
    print("[STARTUP] Systems ready")
    
    print("[APP] Backend ready!")
    
    # Ensure demo user exists
    demo_user = await db.get_user("demo_user")
    if not demo_user:
        print("[APP] Creating demo user...")
        await db.create_user("Demo User", user_id="demo_user")
        # Initialize with dummy stats for chart
        await db.create_session("demo_user", "squat", 45, 3, 120.0, 15.0, 600)
    
    feedback_engine = get_feedback_engine()
    feedback_engine.speak("Coach sportif virtuel prêt!")
    
    yield
    
    # Shutdown
    print("[APP] Shutting down...")
    get_pose_detector().cleanup()
    feedback_engine.shutdown()


# ==================== FastAPI App ====================

app = FastAPI(
    title="Virtual Sports Coach API",
    description="Backend API for real-time pose detection and workout tracking",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend connection
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
#     allow_credentials=True,
# )
print("[STARTUP] Adding CORS middleware...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://192.168.*.*",      # For local network if testing on phone
        "*"                        # Wildcard — remove later for security
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Force OPTIONS responses for all routes (fixes flaky preflights)
@app.options("/{full_path:path}")
async def options_route():
    return {}

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000",
#         "http://127.0.0.1:3000",
#         "http://localhost:8000",
#         "*"   # Wildcard — safe in LOCAL dev only (remove before production!)
#     ],
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
#     allow_headers=["*"],
#     expose_headers=["*"],
#     max_age=600,  # Cache preflight for 10 min
# )
# explicit OPTIONS handler for /users (sometimes helps buggy browsers)
@app.options("/users")
@app.options("/users/{path:path}")
async def cors_options():
    return {}

# ==================== Health & Status ====================

@app.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    pose_detector = get_pose_detector()
    exercise_engine = get_exercise_engine()
    
    return HealthCheck(
        status="ok",
        version="1.0.0",
        camera_available=pose_detector.is_camera_available(),
        models_loaded={
            "pose_detector": True,
            "lstm_model": lstm_model is not None,
            "correction_model": exercise_engine.correction_model is not None,
            "fitness_model": exercise_engine.fitness_model is not None,
        }
    )


@app.get("/status")
async def get_status():
    """Get system status."""
    pose = get_pose_detector()
    hw = get_hardware_manager()
    ex = get_exercise_engine()
    
    return {
        "camera": {
            "connected": pose.is_running,
            "fps": pose.fps
        },
        "hardware": hw.get_status(),
        "models": {
            "lstm": lstm_model is not None,
            "correction": ex.correction_model is not None,
            "fitness": ex.fitness_model is not None
        }
    }


# ==================== User Management ====================

@app.get("/users", response_model=List[UserProfile])
async def read_users():
    """Get all users."""
    users = await db.get_all_users()
    return users


@app.post("/users", response_model=UserProfile)
async def create_new_user(user: UserCreate):
    """Create a new user."""
    # Create new user with auto-generated ID
    new_user = await db.create_user(user.name)
    return new_user


@app.get("/users/{user_id}", response_model=UserProfile)
async def read_user(user_id: str):
    """Get specific user."""
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user."""
    if user_id == "demo_user":
        raise HTTPException(status_code=403, detail="Cannot delete demo user")
        
    result = await db.delete_user(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success", "message": f"User {user_id} deleted"}


# ==================== Session Management ====================

@app.get("/sessions/{user_id}", response_model=SessionSummary)
async def read_sessions(user_id: str, limit: int = 50):
    """Get user sessions."""
    # Verify user exists
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    sessions = await db.get_user_sessions(user_id, limit)
    stats = await db.get_user_stats(user_id)
    
    return SessionSummary(
        user_id=user_id,
        total_sessions=stats["total_sessions"],
        total_reps=stats["total_reps"],
        total_calories=stats["total_calories"],
        avg_fatigue=stats["avg_fatigue"],
        sessions=[SessionData(**s) for s in sessions]
    )


@app.get("/debug/camera_indices")
async def debug_camera_indices():
    """Test and list available camera indices."""
    available_cameras = []
    # Test first 5 indices
    for i in range(5):
        # Try DSHOW
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if not cap.isOpened():
            # Try default
            cap = cv2.VideoCapture(i)
            
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_cameras.append({
                    "id": i,
                    "status": "ready",
                    "info": f"Camera {i} is available and sending frames"
                })
            else:
                available_cameras.append({
                    "id": i,
                    "status": "partial",
                    "info": f"Camera {i} opened but failed to read frame"
                })
            cap.release()
            
    return {
        "available_cameras": available_cameras,
        "current_camera_status": get_pose_detector().is_running,
        "info": "Tested first 5 indices with DSHOW and Default backends."
    }


# ==================== Video Stream ====================

async def generate_frames(cam_id: int = 0):
    """Generate MJPEG frames from pose detector."""
    pose_detector = get_pose_detector()
    
    print(f"[FEED] Starting MJPEG stream loop for camera {cam_id}")
    
    # Try to start camera if not running (non-blocking)
    if not pose_detector.is_running:
        pose_detector.start_camera(camera_id=cam_id)
        
    retry_count = 0
    while True:
        success, frame = pose_detector.get_frame()
        
        if not success or frame is None:
            # yield a "Loading" frame if we've been waiting too long
            retry_count += 1
            if retry_count > 5:
                # Create a black frame with "Loading..." text
                loading_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                # Flip the text so it looks correct when the frontend mirrors it
                cv2.putText(loading_frame, f"Chargement Camera {cam_id}...", (150, 240), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                loading_frame = cv2.flip(loading_frame, 1) # Mirror it now
                
                ret, buffer = cv2.imencode('.jpg', loading_frame)
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            await asyncio.sleep(0.5) # Wait for camera to warm up
            continue
            
        retry_count = 0 # Reset
        
        # Diagnostic: Check brightness
        mean_brightness = np.mean(frame)
        if mean_brightness < 5:
            cv2.putText(frame, "VIDEO TROP NOIRE - VERIFIEZ CACHE CAM!", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
        # Draw timestamp
        cv2.putText(frame, time.strftime("%H:%M:%S"), (50, 450), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
        # Draw skeleton if pose available
        if pose_detector.latest_result:
            frame = pose_detector.draw_pose(frame)
            
        # Optimize size
        frame = cv2.resize(frame, (640, 480))
            
        # Encode
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        if not ret:
            await asyncio.sleep(0.01)
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
               
        await asyncio.sleep(0.033) # Limit to ~30 FPS

@app.get("/video_feed")
async def video_feed(cam_id: int = 0):
    """Stream video with pose overlay. Follows auto-detection if it happens."""
    pose_detector = get_pose_detector()
    
    # Check if we should manually switch or if auto-detection already switched it
    current_active_id = getattr(pose_detector, 'camera_id', 0)
    
    # If the user requested a specific ID AND it's different from current, AND we're not using auto-detection
    if current_active_id != cam_id and not pose_detector.is_running:
        print(f"[FEED] Starting camera {cam_id} as requested.")
        pose_detector.start_camera(camera_id=cam_id)
    elif not pose_detector.is_running:
        print(f"[FEED] Camera not running, starting {cam_id}")
        pose_detector.start_camera(camera_id=cam_id)
        
    # We yield the frames from whatever camera is CURRENTLY working in the singleton
    return StreamingResponse(
        generate_frames(getattr(pose_detector, 'camera_id', cam_id)),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/video_frame")
async def get_video_frame(cam_id: int = 0):
    """
    Get a single frame for manual fetching (fixes ngrok issues).
    """
    pose_detector = get_pose_detector()
    
    # Ensure camera is running
    if not pose_detector.is_running:
         pose_detector.start_camera(camera_id=cam_id)
         
    success, frame = pose_detector.get_frame()
    
    if not success or frame is None:
        # Create a black frame with "Loading..." text
        loading_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(loading_frame, "Initialisation...", (150, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        loading_frame = cv2.flip(loading_frame, 1)
        frame = loading_frame
    else:
        # Draw skeleton if pose available
        if pose_detector.latest_result:
            frame = pose_detector.draw_pose(frame)
        # Resize for performance
        frame = cv2.resize(frame, (640, 480))

    # Encode to JPEG
    ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
    if not ret:
        raise HTTPException(500, "Encoding failed")
        
    return StreamingResponse(
        io.BytesIO(buffer.tobytes()), 
        media_type="image/jpeg"
    )


# ==================== Profile Endpoints ====================

@app.post("/profile", response_model=APIResponse, status_code=201)
async def create_profile(user: UserCreate):
    """Create a new user profile."""
    try:
        user_data = await db.create_user(user.name)
        return APIResponse(
            success=True,
            message="Profile created successfully",
            data=user_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile by ID."""
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/profile/{user_id}")
async def update_profile(user_id: str, update: UserUpdate):
    """Update user profile."""
    success = await db.update_user(
        user_id,
        name=update.name,
        ratios=update.ratios,
        thresholds=update.thresholds,
        body_type=update.body_type.value if update.body_type else None
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True, "message": "Profile updated"}


@app.get("/profiles")
async def list_profiles():
    """List all user profiles."""
    users = await db.get_all_users()
    return {"users": users, "count": len(users)}


@app.delete("/profile/{user_id}")
async def delete_profile(user_id: str):
    """Delete a user profile."""
    success = await db.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "message": "Profile deleted"}


# ==================== Calibration Endpoint ====================

@app.post("/calibrate")
async def calibrate(request: CalibrationRequest):
    """
    Run T-pose calibration for a user.
    Captures keypoints for specified duration and calculates body ratios.
    """
    # Verify user exists
    user = await db.get_user(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Run calibration
    feedback = get_feedback_engine()
    feedback.speak(f"Calibration démarrée. Restez en position T pendant {request.duration_seconds} secondes.")
    
    result = await run_calibration_async(request.duration_seconds)
    
    if result["success"]:
        # Save ratios to user profile
        await db.update_user(
            request.user_id,
            ratios=result["ratios"],
            thresholds=result["thresholds"]
        )
        
        # Estimate body type (use ONNX model result if available from calibration)
        exercise_engine = get_exercise_engine()
        body_type = result.get("body_type") or exercise_engine.estimate_body_type(result["ratios"])
        if body_type:
            await db.update_user(request.user_id, body_type=body_type)
            result["body_type"] = body_type
        
        feedback.speak("Calibration réussie! Vos seuils personnalisés sont appliqués.")
    else:
        feedback.speak("Calibration échouée. Veuillez réessayer.")
    
    return CalibrationResult(
        success=result["success"],
        user_id=request.user_id,
        ratios=result.get("ratios"),
        thresholds=result.get("thresholds"),
        body_type=result.get("body_type"),
        message=result["message"]
    )


# ==================== History Endpoints ====================

@app.get("/history/{user_id}", response_model=SessionSummary)
async def get_history(user_id: str, limit: int = 50):
    """Get workout history for a user."""
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sessions = await db.get_user_sessions(user_id, limit)
    stats = await db.get_user_stats(user_id)
    
    return SessionSummary(
        user_id=user_id,
        total_sessions=stats["total_sessions"],
        total_reps=stats["total_reps"],
        total_calories=stats["total_calories"],
        avg_fatigue=stats["avg_fatigue"],
        sessions=[SessionData(**s) for s in sessions]
    )


@app.post("/session")
async def save_session(
    user_id: str,
    exercise: str,
    reps: int,
    sets: int = 1,
    calories: float = 0,
    fatigue: float = 0,
    duration: int = 0
):
    """Save a workout session."""
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    session_id = await db.create_session(
        user_id, exercise, reps, sets, calories, fatigue, duration
    )
    
    return {"success": True, "session_id": session_id}


# ==================== WebSocket Connection ====================

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[WS] Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time pose streaming.
    
    Client Messages:
    - {"type": "start_session", "data": {"user_id": "...", "exercises": [...]}}
    - {"type": "stop_session"}
    - {"type": "start_calibration", "data": {"user_id": "...", "duration": 5}}
    - {"type": "pause"}
    - {"type": "resume"}
    
    Server Messages:
    - {"type": "keypoints", "data": {...}}
    - {"type": "exercise_update", "data": {...}}
    - {"type": "feedback", "data": {...}}
    - {"type": "rep_count", "data": {"count": N}}
    - {"type": "hardware_status", "data": {...}}
    """
    await manager.connect(websocket)
    
    # Get components
    pose_detector = get_pose_detector()
    exercise_engine = get_exercise_engine()
    feedback_engine = get_feedback_engine()
    hardware = get_hardware_manager()
    
    # Session state
    session_active = False
    session_paused = False
    current_user_id: Optional[str] = None
    current_exercises: List[str] = []
    current_exercise_idx = 0
    session_start_time = 0
    exercise_start_time = 0
    target_reps = 15
    target_sets = 3
    current_set = 1
    total_session_reps = 0
    calories_at_exercise_start = 0.0
    active_session_id = None # Tracks the current database record for the activity
    last_processed_id = -1
    last_feedback_time = 0
    last_feedback_msg = ""
    session_resting = False
    
    async def save_session_data():
        nonlocal current_user_id, session_active, exercise_start_time, total_session_reps, calories_at_exercise_start, active_session_id
        if not session_active or not current_user_id:
            return
            
        try:
            duration = int(time.time() - (exercise_start_time or session_start_time))
            hw_status = hardware.get_status()
            
            # Calculate calories for THIS exercise segment
            total_calories_so_far = hw_status["calories_burned"]
            exercise_calories = max(0.0, total_calories_so_far - calories_at_exercise_start)
            
            _, fatigue_pct = exercise_engine.detect_fatigue()
            
            ex_name = current_exercises[current_exercise_idx] if current_exercises else "unknown"
            reps = getattr(exercise_engine.state, 'total_reps', exercise_engine.state.rep_count)
            
            # Upsert logic
            if active_session_id:
                # Update existing record
                await db.update_session(
                    active_session_id,
                    reps=reps,
                    sets=current_set,
                    calories_est=round(exercise_calories, 3),
                    fatigue_score=fatigue_pct,
                    duration=duration
                )
                print(f"[DB-DEBUG] Updated session {active_session_id}: {ex_name}, {reps} reps")
            elif reps > 0 or duration > 30: # Stricter clutter filter (30s)
                # Create initial record
                active_session_id = await db.create_session(
                    current_user_id,
                    ex_name,
                    reps,
                    current_set,
                    round(exercise_calories, 1),
                    fatigue_pct,
                    duration
                )
                print(f"[DB-DEBUG] Created session {active_session_id} for {ex_name}, {reps} reps")
            else:
                # Skip saving 0-rep, short-duration exercises
                pass
        except Exception as e:
            print(f"[WS-ERR] Failed to auto-save session: {e}")
    
    try:
        # Start camera - DISABLED by default to prevent conflict with Frontend PC Mode
        # if not pose_detector.is_running:
        #     pose_detector.start_camera()
        
        while True:
            try:
                # Check for incoming messages (non-blocking)
                try:
                    message_data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=0.01
                    )
                    message = json.loads(message_data)
                except asyncio.TimeoutError:
                    # No message, continue loop (to send frames if needed)
                    pass
                except WebSocketDisconnect:
                    print("[WS] Client disconnected inside loop")
                    break
                except Exception as e:
                    # print(f"[WS] Error receiving message: {e}")
                    pass
                else:
                    # Process message
                    if message and isinstance(message, dict):
                        msg_type = message.get("type", "")
                        msg_data = message.get("data", {})
                    
                    if msg_type == "start_camera":
                        print("[WS] Client requested camera start")
                        cam_id = msg_data.get("camera_id", 0)
                        pose_detector.start_camera(camera_id=cam_id)
                        await websocket.send_json({"type": "camera_started", "data": {"camera_id": cam_id}})

                    elif msg_type == "stop_camera":
                        print("[WS] Client requested camera stop")
                        pose_detector.stop_camera()
                        await websocket.send_json({"type": "camera_stopped"})

                    elif msg_type == "start_session":
                        current_user_id = msg_data.get("user_id")
                        current_exercises = msg_data.get("exercises", ["squat"])
                        current_exercise_idx = 0
                        
                        # Store per-exercise configs if provided
                        exercise_configs = msg_data.get("exercise_configs", [])
                        print(f"[WS] Received exercise_configs: {exercise_configs}")
                        
                        # Default global targets
                        default_target_reps = msg_data.get("target_reps", 15)
                        default_target_sets = msg_data.get("target_sets", 3)
                        
                        # Set current targets based on config or defaults
                        if exercise_configs and len(exercise_configs) > 0:
                            target_reps = exercise_configs[0].get("reps", default_target_reps)
                            target_sets = exercise_configs[0].get("sets", default_target_sets)
                        else:
                            target_reps = default_target_reps
                            target_sets = default_target_sets
                        
                        current_set = 1
                        
                        session_active = True
                        session_paused = False
                        session_start_time = time.time()
                        exercise_start_time = session_start_time
                        calories_at_exercise_start = 0.0
                        total_session_reps = 0
                        active_session_id = None
                        session_resting = False
                        
                        exercise_engine.reset()
                        
                        # Apply personalized thresholds if user exists
                        if current_user_id:
                            user_data = await db.get_user(current_user_id)
                            if user_data and user_data.get("thresholds"):
                                exercise_engine.apply_custom_thresholds(user_data["thresholds"])
                                print(f"[WS] Loaded personalized thresholds for user {current_user_id}")
                        
                        # Reset feedback cache for a clean state
                        last_feedback_msg = None
                        last_feedback_time = 0
                        
                        hardware.start_session()
                        
                        # First exercise set
                        first_ex = current_exercises[0]
                        feedback_engine.speak(f"Séance démarrée! Premier exercice: {first_ex}")
                        print(f"[WS] Session started for user {current_user_id} with {len(current_exercises)} exercises. Initial targets: {target_reps} reps, {target_sets} sets")
                        
                        await websocket.send_json({
                            "type": "session_started",
                            "data": {
                                "user_id": current_user_id,
                                "exercises": current_exercises,
                                "current_exercise": first_ex,
                                "target_reps": target_reps,
                                "target_sets": target_sets
                            }
                        })

                    elif msg_type == "select_exercise":
                        idx = msg_data.get("index", 0)
                        if 0 <= idx < len(current_exercises):
                            ex_name = current_exercises[idx]
                            
                            # Save previous exercise data before switching
                            reps_to_add = exercise_engine.state.total_reps
                            total_session_reps += reps_to_add
                            print(f"[SESSION-DEBUG] Manual switch addition: {reps_to_add}. Total: {total_session_reps}")
                            await save_session_data()
                            
                            current_exercise_idx = idx
                            current_set = 1
                            session_resting = False
                            exercise_engine.reset()
                            exercise_start_time = time.time()
                            active_session_id = None
                            
                            # Update targets for the new exercise
                            if exercise_configs and idx < len(exercise_configs):
                                target_reps = exercise_configs[idx].get("reps", default_target_reps)
                                target_sets = exercise_configs[idx].get("sets", default_target_sets)
                            
                            # Don't reset calories_at_start here, as calories are global for session
                            # But we want to track current exercise calories
                            calories_at_exercise_start = hardware.get_status()["calories_burned"]
                            
                            # Reset feedback cache to allow immediate new messages
                            last_feedback_msg = None
                            last_feedback_time = 0
                            
                            ex_name = current_exercises[idx]
                            feedback_engine.speak(f"Exercice suivant: {ex_name}")
                            print(f"[WS] Exercise switched to: {ex_name} (index {idx}). New targets: {target_reps} reps, {target_sets} sets")
                            await websocket.send_json({
                                "type": "exercise_change",
                                "data": {
                                    "index": idx, 
                                    "name": ex_name, 
                                    "immediate": True,
                                    "target_reps": target_reps,
                                    "target_sets": target_sets
                                }
                            })
                
                    elif msg_type == "stop_session":
                        # Final save (update total session reps with current exercise reps)
                        reps_to_add = exercise_engine.state.total_reps
                        total_session_reps += reps_to_add
                        print(f"[SESSION-DEBUG] Added {reps_to_add} reps to total. New total: {total_session_reps}")
                        await save_session_data()
                        
                        session_active = False
                        hardware.stop_session()
                        
                        duration_total = int(time.time() - session_start_time)
                        hw_status = hardware.get_status()
                        
                        feedback_engine.session_complete(
                            total_session_reps,
                            hw_status["calories_burned"],
                            duration_total // 60
                        )
                        
                        await websocket.send_json({
                            "type": "session_stopped",
                            "data": {
                                "total_reps": total_session_reps,
                                "total_sets": current_set,
                                "calories": int(hw_status["calories_burned"])
                            }
                        })
                    
                    elif msg_type == "pause":
                        session_paused = True
                        await websocket.send_json({"type": "paused"})
                    
                    elif msg_type == "resume":
                        session_paused = False
                        session_resting = False
                        await websocket.send_json({"type": "resumed"})
                    
                    elif msg_type == "start_calibration":
                        user_id = msg_data.get("user_id")
                        duration = msg_data.get("duration", 5)
                        
                        print(f"[WS] Starting async calibration for user {user_id}")
                        calibrator = Calibrator(CalibrationConfig(duration_seconds=float(duration)))
                        
                        # Use the async generator for progress updates
                        async for update in calibrator.calibrate_stream(pose_detector):
                            if update["type"] == "progress":
                                await websocket.send_json({
                                    "type": "calibration_progress",
                                    "data": {
                                        "progress": update["progress"],
                                        "status": update["status"],
                                        "collected": update.get("collected", 0),
                                        "total": update.get("total", 0)
                                    }
                                })
                            elif update["type"] == "result":
                                result = update
                                if result["success"] and user_id:
                                    # Save everything to DB
                                    await db.update_user(
                                        user_id,
                                        ratios=result["ratios"],
                                        thresholds=result["thresholds"]
                                    )
                                    
                                    # Also save body type from ONNX
                                    if result.get("body_type"):
                                        await db.update_user(user_id, body_type=result["body_type"])
                                        print(f"[WS] Calibration saved with body type: {result['body_type']}")

                                await websocket.send_json({
                                    "type": "calibration_complete",
                                    "data": result
                                })
                                break
                
            
                # Process pose if session active and not paused
                # Always capture frame and detect pose if camera is "running" (passive or active)
                success, frame = pose_detector.get_frame()
                
                if success:
                    # In PC mode (camera_id == -1), frames are pushed via push_external_frame.
                    # The dedicated worker thread in PoseDetector handles detection asynchronously.
                    # We strictly use the latest_result and only if it's FRESH.
                    pose_data = pose_detector.latest_result
                    
                    if pose_data and pose_data.get("result_id", 0) > last_processed_id:
                        last_processed_id = pose_data["result_id"]

                        # Calculate average visibility
                        vis_scores = [kpt.get("visibility", 0) for kpt in pose_data.get("keypoints", {}).values()]
                        avg_visibility = sum(vis_scores) / len(vis_scores) if vis_scores else 0
                        
                        # Forward any voice messages from the engine
                        voice_messages = feedback_engine.get_ws_messages()
                        for msg in voice_messages:
                            await websocket.send_json({"type": "voice", "data": {"text": msg}})

                        # 1. Send keypoints to frontend (Only on fresh result)
                        keypoints_to_send = {}
                        for k, v in pose_data.get("keypoints", {}).items():
                            name = (POSE_LANDMARKS.get(int(k)) if (isinstance(k, int) or (isinstance(k, str) and k.isdigit())) else k)
                            if isinstance(v, dict) and "normalized" in v:
                                keypoints_to_send[name] = {
                                    "x": v["normalized"]["x"],
                                    "y": v["normalized"]["y"],
                                    "visibility": v.get("visibility", 1.0)
                                }
                        
                        await websocket.send_json({
                            "type": "keypoints",
                            "data": {
                                "keypoints": keypoints_to_send,
                                "angles": pose_data.get("angles", {}),
                                "fps": round(pose_detector.fps, 1)
                            }
                        })

                        # 2. Session Logic (Only if active and NOT in rest period)
                        if session_active and not session_paused and not session_resting:
                            # Update exercise engine
                            current_exercise_name = current_exercises[current_exercise_idx] if current_exercises else None
                            # Robust mapping: normalize name (handle both frontend IDs and direct names)
                            search_name = (current_exercise_name.lower().replace("-", "_") 
                                          if current_exercise_name else None)
                            exercise_type = map_exercise_name(search_name)
                            
                            angles = pose_data.get("angles", {})
                            try:
                                exercise_result = exercise_engine.update(angles, pose_data.get("keypoints", {}), exercise_type, visibility=avg_visibility)
                            except Exception as e:
                                print(f"[EXERCISE-ERR] Update failed: {e}")
                                # Provide a minimal safe result to avoid downstream errors
                                exercise_result = {"exercise": exercise_type.value if exercise_type else "unknown", "events": []}
                            
                            # Send exercise update with ML classification
                            await websocket.send_json({
                                "type": "exercise_update",
                                "data": exercise_result
                            })
                            
                            # Handle events
                            events = exercise_result.get("events", [])
                            
                            for event in events:
                                if event["type"] == "rep_complete":
                                    count = event["count"]
                                    
                                    # Real-time save on EVERY rep!
                                    await save_session_data()
                                    
                                    feedback_engine.rep_feedback(count, target_reps, current_exercise_name or "exercise")
                                    await websocket.send_json({
                                        "type": "rep_count",
                                        "data": {"count": count, "target": target_reps, "set": current_set}
                                    })
                                    if count >= target_reps:
                                        session_resting = True
                                        # Reset feedback on transition to avoid stuck messages
                                        last_feedback_msg = None
                                        last_feedback_time = 0
                                        
                                        if current_set < target_sets:
                                            current_set += 1
                                            exercise_engine.new_set()
                                            feedback_engine.exercise_transition(current_exercises[current_exercise_idx], 60)
                                            await websocket.send_json({"type": "set_complete", "data": {"set": current_set-1, "next_set": current_set}})
                                        elif current_exercise_idx < len(current_exercises) - 1:
                                            # Move to next exercise
                                            reps_to_add = exercise_engine.state.total_reps
                                            total_session_reps += reps_to_add
                                            print(f"[SESSION-DEBUG] Transition addition: {reps_to_add}. Total: {total_session_reps}")
                                            
                                            current_exercise_idx += 1
                                            current_set = 1
                                            exercise_engine.reset()
                                            exercise_start_time = time.time()
                                            active_session_id = None
                                            calories_at_exercise_start = hardware.get_status()["calories_burned"]
                                            
                                            # Update targets for the new exercise
                                            if exercise_configs and current_exercise_idx < len(exercise_configs):
                                                target_reps = exercise_configs[current_exercise_idx].get("reps", default_target_reps)
                                                target_sets = exercise_configs[current_exercise_idx].get("sets", default_target_sets)
                                            else:
                                                target_reps = default_target_reps
                                                target_sets = default_target_sets
                                                
                                            feedback_engine.exercise_transition(current_exercises[current_exercise_idx], 60)
                                            await websocket.send_json({
                                                "type": "exercise_change", 
                                                "data": {
                                                    "index": current_exercise_idx,
                                                    "target_reps": target_reps,
                                                    "target_sets": target_sets
                                                }
                                            })
                                        else:
                                            # Final exercise completed!
                                            reps_to_add = exercise_engine.state.total_reps
                                            total_session_reps += reps_to_add
                                            print(f"[SESSION-DEBUG] Final completion addition: {reps_to_add}. Total: {total_session_reps}")
                                            await save_session_data()
                                            
                                            hw_status = hardware.get_status()
                                            feedback_engine.session_complete(total_session_reps, hw_status["calories_burned"], 0)
                                            await websocket.send_json({
                                                "type": "session_stopped",
                                                "data": {
                                                    "total_reps": total_session_reps,
                                                    "total_sets": current_set,
                                                    "calories": int(hw_status["calories_burned"])
                                                }
                                            })
                                            session_active = False
                                
                                    else:
                                        # Only process if not resting (this is also handled by the main check above)
                                        pass
                                    
                                if session_resting:
                                    # Check for resume signal or simply wait for next frame processing
                                    # For now, let's keep it simple: the next frame will just skip until set_complete/exercise_change resets it
                                    # Actually, let's add a reset for session_resting when the frontend skips rest
                                    pass

                                elif event["type"] in ["form_warning", "rep_rejected"]:
                                    pass # Handled by prioritized logic below
                            
                            # --- Continuous Feedback Decisions (Prioritized) ---
                            current_time = time.time()
                            feedback_data = None
                            
                            # Find any form issues in events
                            form_issues = next((e.get("issues", []) for e in events if e["type"] == "form_warning"), [])
                            
                            # Include ML classification in feedback if available
                            ml_label = exercise_result.get("ml_label")
                            ml_conf = exercise_result.get("ml_confidence")
                            
                            if ml_label and ml_conf and ml_conf > 0.8:
                                # Use ML classification as primary feedback for squat/pushup
                                if "Correct" in ml_label:
                                    feedback_data = {"status": "perfect", "message": ml_label, "ml_class": ml_label, "ml_confidence": ml_conf}
                                else:
                                    feedback_data = {"status": "warning", "message": ml_label, "ml_class": ml_label, "ml_confidence": ml_conf, "issues": [ml_label.lower().replace(" ", "_")]}
                            elif form_issues:
                                message = POSTURE_MESSAGES.get(form_issues[0], "Vérifiez votre posture!")
                                feedback_data = {"status": "warning", "message": message, "issues": form_issues}
                            elif avg_visibility < 0.6:
                                message = POSTURE_MESSAGES.get("body_not_visible", "Reculez un peu!")
                                feedback_data = {"status": "warning", "message": message}
                            elif exercise_result.get("form_quality", 0) > 0.9:
                                feedback_data = {"status": "perfect", "message": "Posture parfaite"}
                            elif last_feedback_msg != "Posture OK":
                                feedback_data = {"status": "perfect", "message": "Posture OK"}

                            # --- Throttling Logic ---
                            if feedback_data:
                                new_msg = feedback_data["message"]
                                should_send = False
                                
                                # IMMEDIATE SEND if switching status or message (e.g. clearing a warning)
                                if new_msg != last_feedback_msg:
                                    should_send = True
                                # THROTTLED SEND for repeated same message
                                elif current_time - last_feedback_time > 3.0:
                                    should_send = True
                                
                                if should_send:
                                    if feedback_data["status"] == "warning" and new_msg != last_feedback_msg:
                                        feedback_engine.speak(new_msg)
                                    
                                    await websocket.send_json({"type": "feedback", "data": feedback_data})
                                    last_feedback_time = current_time
                                    last_feedback_msg = new_msg

                            # Fatigue and Hardware
                            is_fatigued, slowdown = exercise_engine.detect_fatigue()
                            if is_fatigued:
                                feedback_engine.fatigue_warning(slowdown)
                                await websocket.send_json({"type": "fatigue_warning", "data": {"slowdown_percent": slowdown}})

                            # 4. Hardware Safety Checks
                            hardware.set_exercise_intensity(0.5 + (exercise_engine.state.rep_count % 5) * 0.1)
                            hw_status = hardware.update()
                            should_pause, reason = hardware.should_pause_exercise()
                            if should_pause:
                                session_paused = True
                                feedback_engine.speak(reason, priority=True)
                                # Use 'paused' type for consistency with manual pauses but include reason
                                await websocket.send_json({"type": "paused", "data": {"reason": reason}})
                    
                    # Ensure we indent correctly for the if pose_data block
                else:
                    # No pose detected - throttle this message to avoid saturating WebSocket
                    if pose_detector.frame_count % 30 == 0:
                        await websocket.send_json({
                            "type": "no_detection",
                            "data": {"message": "Personne non détectée"}
                        })
            
                await asyncio.sleep(0.01)  # Faster loop for better response
            except Exception as e:
                err_msg = str(e).lower()
                # If the socket is closed, we MUST break the loop
                if "close" in err_msg or "closed" in err_msg or "disconnected" in err_msg:
                    print(f"[WS] Connection closed (detected in loop). Stopping.")
                    break
                    
                # Log other errors but KEEP LOOP RUNNING for transient issues
                print(f"[WS] Transient loop error: {e}")
                await asyncio.sleep(0.1) # Cool down
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if session_active:
            await save_session_data()
            hardware.stop_session()
    
    except Exception as e:
        print(f"[WS] Error: {e}")
        manager.disconnect(websocket)
        if session_active:
            await save_session_data()
            hardware.stop_session()


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    # Important: reload=False to ensure stable CORS configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )