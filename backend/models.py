"""
Pydantic models for API validation and WebSocket messages.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class ExerciseType(str, Enum):
    """Supported exercise types"""
    SQUAT = "squat"
    PUSHUP = "pushup"
    PLANK = "plank"
    BICEP_CURL = "bicep_curl"
    LUNGE = "lunge"
    YOGA = "yoga"
    UNKNOWN = "unknown"


class BodyType(str, Enum):
    """Body type classification from fitness_model.onnx"""
    FAT = "fat"
    WEAK = "weak"
    NORMAL = "normal"
    ATHLETIC = "athletic"
    UNKNOWN = "unknown"
    
# Then keep:
body_type: Optional[BodyType] = None

class PostureStatus(str, Enum):
    """Posture quality status"""
    PERFECT = "perfect"
    WARNING = "warning"
    ERROR = "error"


class FeedbackType(str, Enum):
    """Feedback modality types"""
    TEXT = "text"
    VOICE = "voice"
    LED = "led"
    BUZZER = "buzzer"


# ==================== User & Profile ====================

class UserCreate(BaseModel):
    """Request model for creating a new user"""
    name: str = Field(..., min_length=1, max_length=100)


class UserProfile(BaseModel):
    """User profile with calibration data"""
    id: str
    name: str
    ratios: Optional[Dict[str, float]] = None
    thresholds: Optional[Dict[str, float]] = None
    body_type: Optional[BodyType] = None
    created_at: datetime


class UserUpdate(BaseModel):
    """Request model for updating user data"""
    name: Optional[str] = None
    ratios: Optional[Dict[str, float]] = None
    thresholds: Optional[Dict[str, float]] = None
    body_type: Optional[BodyType] = None


# ==================== Calibration ====================

class CalibrationRequest(BaseModel):
    """Request to start calibration"""
    user_id: str
    duration_seconds: int = Field(default=5, ge=3, le=10)


class BodyRatios(BaseModel):
    """Body measurements from T-pose calibration"""
    shoulder_width: float = Field(..., description="Normalized shoulder width")
    arm_length: float = Field(..., description="Arm length ratio")
    leg_length: float = Field(..., description="Leg length ratio")
    torso_height: float = Field(..., description="Torso height ratio")
    leg_torso_ratio: float = Field(..., description="Leg to torso ratio")


class ExerciseThresholds(BaseModel):
    """Personalized angle thresholds for exercises"""
    squat_knee_angle: float = Field(default=90.0, description="Target knee angle for squat")
    squat_tolerance: float = Field(default=10.0, description="Angle tolerance")
    pushup_elbow_angle: float = Field(default=90.0, description="Target elbow angle for pushup")
    plank_hip_angle: float = Field(default=170.0, description="Target hip angle for plank")
    bicep_curl_angle: float = Field(default=45.0, description="Target elbow angle for curl")


class CalibrationResult(BaseModel):
    """Result of T-pose calibration"""
    success: bool
    user_id: str
    ratios: Optional[BodyRatios] = None
    thresholds: Optional[ExerciseThresholds] = None
    body_type: Optional[BodyType] = None
    message: str


# ==================== Keypoints ====================

class Keypoint(BaseModel):
    """Single body keypoint"""
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0
    name: Optional[str] = None


class KeypointFrame(BaseModel):
    """Frame of keypoints from pose detection"""
    timestamp: float
    keypoints: Dict[str, Keypoint]
    angles: Optional[Dict[str, float]] = None


# ==================== Exercise Session ====================

class ExerciseState(BaseModel):
    """Current state of exercise detection"""
    exercise: ExerciseType
    phase: str = Field(default="idle", description="up, down, hold, idle")
    rep_count: int = 0
    set_count: int = 1
    confidence: float = 0.0


class SessionCreate(BaseModel):
    """Request to create a new session"""
    user_id: str
    exercises: List[str] = []


class SessionData(BaseModel):
    """Session history data"""
    id: int
    user_id: str
    date: datetime
    exercise: str
    reps: int
    sets: int
    calories_est: float
    fatigue_score: float
    duration: int  # seconds


class SessionSummary(BaseModel):
    """Summary of user's session history"""
    user_id: str
    total_sessions: int
    total_reps: int
    total_calories: float
    avg_fatigue: float
    sessions: List[SessionData]


# ==================== Feedback ====================

class FeedbackMessage(BaseModel):
    """Feedback to send to user"""
    type: FeedbackType
    text: str
    color: Optional[str] = None  # For LED: "green", "red", "blue", "yellow"
    speak: bool = False  # Whether to use TTS


# ==================== WebSocket Messages ====================

class WSMessageType(str, Enum):
    """WebSocket message types"""
    # Client -> Server
    START_SESSION = "start_session"
    STOP_SESSION = "stop_session"
    START_CALIBRATION = "start_calibration"
    PAUSE = "pause"
    RESUME = "resume"
    
    # Server -> Client
    KEYPOINTS = "keypoints"
    EXERCISE_UPDATE = "exercise_update"
    FEEDBACK = "feedback"
    REP_COUNT = "rep_count"
    FATIGUE_WARNING = "fatigue_warning"
    SESSION_COMPLETE = "session_complete"
    CALIBRATION_PROGRESS = "calibration_progress"
    CALIBRATION_COMPLETE = "calibration_complete"
    HARDWARE_STATUS = "hardware_status"
    ERROR = "error"


class WSMessage(BaseModel):
    """WebSocket message envelope"""
    type: WSMessageType
    data: Dict[str, Any] = {}
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


# ==================== Hardware Simulation ====================

class HardwareStatus(BaseModel):
    """Simulated hardware sensor status"""
    heart_rate: int = Field(default=75, ge=40, le=220)
    heart_rate_warning: bool = False
    imu_tremor_detected: bool = False
    battery_level: int = Field(default=100, ge=0, le=100)
    eco_mode: bool = False
    calories_burned: float = 0.0
    water_glasses_saved: float = 0.0  # Eco message equivalent


# ==================== API Responses ====================

class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[Any] = None


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = "ok"
    version: str = "1.0.0"
    camera_available: bool = False
    models_loaded: Dict[str, bool] = {}
