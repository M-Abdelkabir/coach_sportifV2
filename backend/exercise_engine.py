"""
Exercise detection and rep counting engine.
Uses joint angles to classify exercises and count repetitions.
"""
import pickle
import numpy as np
import onnxruntime as ort
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
import time
import tensorflow as tf  # For TFLite
import joblib  # For scaler

# Path to models
MODELS_DIR = Path(__file__).parent / "models"

# Load Keras LSTM model directly (avoids TFLite Flex delegate issues)
lstm_path = MODELS_DIR / "model_lstm_tache2.h5"
lstm_model = None

if lstm_path.exists():
    try:
        import tensorflow as tf
        lstm_model = tf.keras.models.load_model(str(lstm_path))
        print(f"[EXERCISE] Loaded LSTM model from {lstm_path}")
    except Exception as e:
        print(f"[EXERCISE] Failed to load LSTM model: {e}")
else:
    print(f"[EXERCISE] LSTM model not found at {lstm_path}")

scaler = joblib.load(MODELS_DIR / "scaler_tache2.pkl")

labels_map = {
    0: "Pushup Correct",
    1: "Pushup Incorrect",
    2: "Squat Correct",
    3: "Squat Shallow",
    4: "Squat Forward Lean",
    5: "Squat Knee Caving",
    6: "Squat Heels Off",
    7: "Squat Asymmetric"
}

WINDOW_SIZE = 20
features_buffer: List[np.ndarray] = []
current_exercise_for_buffer: str = ""

class ExerciseType(str, Enum):
    """Supported exercise types."""
    SQUAT = "squat"
    PUSHUP = "pushup"
    PLANK = "plank"
    BICEP_CURL = "bicep_curl"
    LUNGE = "lunge"
    TRICEP_DIP = "tricep_dip"
    SHOULDER_PRESS = "shoulder_press"
    ROW = "row"
    CRUNCH = "crunch"
    DEADLIFT = "deadlift"
    UNKNOWN = "unknown"


class ExercisePhase(str, Enum):
    """Exercise movement phases."""
    IDLE = "idle"
    DOWN = "down"
    UP = "up"
    HOLD = "hold"
    TRANSITION = "transition"


@dataclass
class ExerciseState:
    current_type: ExerciseType = ExerciseType.UNKNOWN
    current_phase: ExercisePhase = ExercisePhase.IDLE
    rep_count: int = 0
    set_count: int = 0
    feedback_codes: List[str] = field(default_factory=list)
    posture_score: float = 1.0
    ml_label: Optional[str] = None
    ml_confidence: float = 0.0
    total_reps: int = 0  # Reconstructed/Accumulated across sets
    
    # Timing for fatigue detection
    rep_times: List[float] = field(default_factory=list)
    last_rep_time: float = 0.0
    avg_rep_time: float = 0.0
    
    # Quality and Visibility tracking
    form_quality: float = 1.0  # 0.0 to 1.0
    form_issues: List[str] = field(default_factory=list)
    visibility: float = 1.0     # Current average visibility
    
    # Tracking for the current repetition (reset each rep)
    min_quality_in_rep: float = 1.0
    min_visibility_in_rep: float = 1.0
    rep_start_time: float = 0.0


@dataclass
class ExerciseThresholds:
    """Angle thresholds for exercise detection."""
    # Squat thresholds
    squat_knee_down: float = 80.0  # Deeper squat (was 90)
    squat_knee_up: float = 165.0   # Full extension (was 160)
    squat_tolerance: float = 10.0  # Tighter tolerance (was 15)
    
    # Push-up thresholds
    pushup_elbow_down: float = 75.0 # More depth (was 90)
    pushup_elbow_up: float = 165.0
    pushup_hip_angle: float = 175.0
    
    # Plank thresholds
    plank_hip_min: float = 170.0 # Flatter body (was 160)
    plank_hip_max: float = 185.0
    plank_hold_time: float = 1.5
    
    # Bicep curl thresholds
    curl_elbow_down: float = 165.0  # Arm extended
    curl_elbow_up: float = 40.0     # Arm curled

    # Tricep dip thresholds
    dip_elbow_down: float = 90.0
    dip_elbow_up: float = 160.0
    
    # Shoulder press thresholds
    press_elbow_down: float = 60.0
    press_elbow_up: float = 160.0
    
    # Row thresholds
    row_elbow_pull: float = 80.0
    row_elbow_extend: float = 160.0
    
    # Crunch thresholds
    crunch_hip_up: float = 100.0   # Torso raised
    crunch_hip_down: float = 150.0 # Laying flat
    
    # Deadlift thresholds
    deadlift_hip_down: float = 100.0 # Bent over
    deadlift_hip_up: float = 160.0   # Standing
    
    # Global quality/timing thresholds
    min_rep_duration: float = 0.8
    min_visibility_threshold: float = 0.5
    min_form_quality_threshold: float = 0.6


class ExerciseEngine:
    """
    Exercise detection and rep counting engine.
    Uses sklearn classifier for exercise classification
    and angle-based rep counting.
    """
    
    def __init__(self):
        """
        Initialize the exercise engine.
        
        Loads all ML models:
        - LSTM (via TFLite) + scaler for pushup/squat form classification
        - correctionExercices ONNX for angle-based correction on other exercises
        - fitness_model ONNX for body type estimation
        """
        self.state = ExerciseState()
        self.prev_angles: Dict[str, float] = {}
        self.thresholds = ExerciseThresholds()
        self.prev_keypoints: Optional[Dict] = None
        
        # Phase tracking (required by _is_rep_complete / update)
        self._prev_phase = ExercisePhase.IDLE
        self._rep_progress_flag = False
        self._phase_start_time = time.time()
        self.confidence = 0.0
        
        # Model slots (populated by _load_models)
        self.classifier = None          # kept for health-check compat; always None now
        self.correction_model = None    # correctionExercices ONNX
        self.fitness_model = None       # fitness_model ONNX
        
        self._load_models()
        print("[EXERCISE] Exercise engine initialized")
    
    def update_thresholds(self, thresholds: Dict):
        """Update personalized thresholds from calibration."""
        self.thresholds = thresholds

    def _calculate_features(self, keypoints: Dict) -> np.ndarray:
        """Extract 15 features from keypoints."""
        from pose_detector import POSE_LANDMARKS  # Import here to avoid circular

        def get_point(idx):
            name = POSE_LANDMARKS[idx]
            point = keypoints.get(name)
            
            if point is None:
                return (0.0, 0.0, 0.0)
            
            if isinstance(point, dict):
                return (point.get('x', 0.0), point.get('y', 0.0), point.get('z', 0.0))
            return (point[0], point[1], point[2])

        def calculate_angle(a, b, c):
            a, b, c = np.array(a), np.array(b), np.array(c)
            ba = a - b
            bc = c - b
            cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
            return angle

        def calculate_distance(a, b):
            return np.linalg.norm(np.array(a) - np.array(b))

        # Angles
        left_elbow = calculate_angle(get_point(11), get_point(13), get_point(15))
        right_elbow = calculate_angle(get_point(12), get_point(14), get_point(16))
        left_shoulder = calculate_angle(get_point(13), get_point(11), get_point(23))
        right_shoulder = calculate_angle(get_point(14), get_point(12), get_point(24))
        left_hip = calculate_angle(get_point(11), get_point(23), get_point(25))
        right_hip = calculate_angle(get_point(12), get_point(24), get_point(26))
        left_knee = calculate_angle(get_point(23), get_point(25), get_point(27))
        right_knee = calculate_angle(get_point(24), get_point(26), get_point(28))
        left_ankle = calculate_angle(get_point(25), get_point(27), get_point(31))
        right_ankle = calculate_angle(get_point(26), get_point(28), get_point(32))
        # Midpoint of shoulders for back angle (needs to be 3D)
        p11 = get_point(11)
        p12 = get_point(12)
        mid_shoulder = ((p11[0] + p12[0])/2, (p11[1] + p12[1])/2, (p11[2] + p12[2])/2)
        back = calculate_angle(p11, mid_shoulder, get_point(23))

        # Derived
        knee_dist = calculate_distance(get_point(25), get_point(26))
        left_heel = abs(get_point(27)[2] - get_point(31)[2])
        right_heel = abs(get_point(28)[2] - get_point(32)[2])
        asymmetry = abs(left_knee - right_knee) + abs(left_hip - right_hip)

        features = np.array([
            left_elbow, right_elbow, left_shoulder, right_shoulder,
            left_hip, right_hip, left_knee, right_knee,
            left_ankle, right_ankle, back, knee_dist,
            left_heel, right_heel, asymmetry
        ])
        return features

    def _run_lstm_quality_check(self, keypoints: Dict) -> Tuple[Optional[str], float]:
        global features_buffer, current_exercise_for_buffer

        if lstm_model is None:
            return None, 0.0

        # Only for squat and pushup
        if self.state.current_type not in [ExerciseType.SQUAT, ExerciseType.PUSHUP]:
            return None, 0.0

        # Clear buffer if exercise changed
        ex_name = self.state.current_type.value
        if ex_name != current_exercise_for_buffer:
            features_buffer.clear()
            current_exercise_for_buffer = ex_name

        # Compute your 15 features (this part must match your training!)
        features = self._calculate_features(keypoints)

        features_buffer.append(features)
        if len(features_buffer) > WINDOW_SIZE:
            features_buffer = features_buffer[-WINDOW_SIZE:]

        if len(features_buffer) < WINDOW_SIZE:
            return None, 0.0

        try:
            # Prepare input: (1, 20, 15)
            data_raw = np.array(features_buffer)
            data_scaled = scaler.transform(data_raw)
            input_data = np.expand_dims(data_scaled, axis=0)

            prediction = lstm_model.predict(input_data, verbose=0)[0]
            class_idx = np.argmax(prediction)
            confidence = float(np.max(prediction))

            if confidence >= 0.80:
                label = labels_map[class_idx]
                
                # Filter label by current exercise type to avoid mismatch (e.g., Pushup label during Squat)
                if self.state.current_type == ExerciseType.SQUAT and "Squat" in label:
                    return label, confidence
                if self.state.current_type == ExerciseType.PUSHUP and "Pushup" in label:
                    return label, confidence
        except Exception as e:
            print(f"[LSTM] Inference error: {e}")
        
        return None, 0.0

    def _ml_classify(self, features: np.ndarray) -> Tuple[Optional[str], float]:
        """Run LSTM classification."""
        global features_buffer
        features_buffer.append(features)
        if len(features_buffer) > WINDOW_SIZE:
            features_buffer = features_buffer[-WINDOW_SIZE:]

        if len(features_buffer) == WINDOW_SIZE:
            data_scaled = scaler.transform(np.array(features_buffer))
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            interpreter.set_tensor(input_details[0]['index'], np.expand_dims(data_scaled.astype(np.float32), axis=0))
            interpreter.invoke()
            prediction = interpreter.get_tensor(output_details[0]['index'])[0]
            class_idx = np.argmax(prediction)
            confidence = np.max(prediction)
            if confidence > 0.85:
                return labels_map[class_idx], confidence
        return None, 0.0

    def process_keypoints(self, keypoints: Dict) -> Dict:
        """Process keypoints to detect exercise, phase, reps, and feedback."""
        angles = self._calculate_angles(keypoints)

        # === LSTM quality check for pushup / squat ===
        if self.state.current_type in [ExerciseType.SQUAT, ExerciseType.PUSHUP]:
            ml_label, ml_conf = self._run_lstm_quality_check(keypoints)
            if ml_label:
                self.state.ml_label = ml_label
                self.state.ml_confidence = ml_conf
                
                # If LSTM says bad form → add to feedback
                if "Incorrect" in ml_label or any(issue in ml_label.lower() for issue in ["shallow", "lean", "caving", "off", "asymmetric"]):
                    issue_code = ml_label.lower().replace(" ", "_")
                    if issue_code not in self.state.feedback_codes:
                        self.state.feedback_codes.append(issue_code)
        else:
            # === Correction ONNX for all other exercises ===
            corr_label, corr_conf = self._run_correction_onnx(keypoints)
            if corr_label:
                self.state.ml_label = corr_label
                self.state.ml_confidence = corr_conf
                issue_code = corr_label.lower().replace(" ", "_")
                if issue_code not in self.state.feedback_codes:
                    self.state.feedback_codes.append(issue_code)
        
        self.prev_keypoints = keypoints
        return {
            "exercise": self.state.current_type.value,
            "phase": self.state.current_phase.value,
            "rep_count": self.state.rep_count,
            "feedback_codes": self.state.feedback_codes,
            "ml_label": self.state.ml_label,
            "ml_confidence": self.state.ml_confidence
        }

    def _load_models(self):
        """Load ML models: correction ONNX + fitness ONNX.
        
        LSTM / scaler are loaded at module level (global interpreter & scaler).
        classif_model_.pkl is no longer used — exercise type comes from the
        frontend UI selection and the LSTM handles pushup/squat form quality.
        """
        # --- 1. correctionExercices ONNX (angle-based correction for non-LSTM exercises) ---
        correction_path = MODELS_DIR / "correctionExercices (1).onnx"
        if correction_path.exists():
            try:
                self.correction_model = ort.InferenceSession(
                    str(correction_path),
                    providers=['CPUExecutionProvider']
                )
                print(f"[EXERCISE] Loaded correction model from {correction_path}")
            except Exception as e:
                print(f"[EXERCISE] Failed to load correction model: {e}")
                self.correction_model = None
        else:
            print(f"[EXERCISE] Correction model not found at {correction_path}")
        
        # --- 2. fitness_model ONNX (body type estimation) ---
        fitness_path = MODELS_DIR / "fitness_model.onnx"
        if fitness_path.exists():
            try:
                self.fitness_model = ort.InferenceSession(
                    str(fitness_path),
                    providers=['CPUExecutionProvider']
                )
                print(f"[EXERCISE] Loaded fitness model from {fitness_path}")
            except Exception as e:
                print(f"[EXERCISE] Failed to load fitness model: {e}")
                self.fitness_model = None
        else:
            print(f"[EXERCISE] Fitness model not found at {fitness_path}")
    
    def _run_correction_onnx(self, keypoints: Dict) -> Tuple[Optional[str], float]:
        """Run correctionExercices ONNX model for form correction.
        
        NOTE: This model expects image inputs [1, 3, 320, 320]. 
        Since this engine only has access to keypoints/angles, we skip 
        inference to avoid rank mismatch errors.
        """
        # Model is image-based, skipping scalar inference
        return None, 0.0
    
    def classify_exercise(self, angles: Dict[str, float]) -> Tuple[ExerciseType, float]:
        """
        Classify the current exercise from joint angles.
        Uses rule-based classification. Exercise type is normally provided
        by the frontend UI, so this is a fallback for auto-detection.
        
        Args:
            angles: Dictionary of joint angles
            
        Returns:
            Tuple of (exercise_type, confidence)
        """
        return self._rule_based_classification(angles)
    
    def _prepare_features(self, angles: Dict[str, float]) -> Optional[np.ndarray]:
        """Prepare feature vector for classifier."""
        required_angles = [
            "left_elbow", "right_elbow",
            "left_knee", "right_knee",
            "left_hip", "right_hip",
            "left_shoulder", "right_shoulder"
        ]
        
        features = []
        for angle_name in required_angles:
            if angle_name in angles:
                features.append(angles[angle_name])
            else:
                return None  # Missing required angle
        
        # Add derived features
        if "torso_angle" in angles:
            features.append(angles["torso_angle"])
        
        return np.array(features)
    
    def _map_prediction_to_exercise(self, prediction) -> ExerciseType:
        """Map classifier prediction to ExerciseType."""
        mapping = {
            0: ExerciseType.SQUAT,
            1: ExerciseType.PUSHUP,
            2: ExerciseType.PLANK,
            3: ExerciseType.BICEP_CURL,
            4: ExerciseType.LUNGE,
            "squat": ExerciseType.SQUAT,
            "pushup": ExerciseType.PUSHUP,
            "pompe": ExerciseType.PUSHUP,
            "plank": ExerciseType.PLANK,
            "planche": ExerciseType.PLANK,
            "bicep": ExerciseType.BICEP_CURL,
            "curl": ExerciseType.BICEP_CURL,
            "lunge": ExerciseType.LUNGE,
            "fente": ExerciseType.LUNGE,
            # New exercises mapping
            "tricep_dip": ExerciseType.TRICEP_DIP,
            "tricep-dips": ExerciseType.TRICEP_DIP,
            "tricep_dips": ExerciseType.TRICEP_DIP,
            "dips": ExerciseType.TRICEP_DIP,
            "shoulder_press": ExerciseType.SHOULDER_PRESS,
            "shoulder-press": ExerciseType.SHOULDER_PRESS,
            "press": ExerciseType.SHOULDER_PRESS,
            "militaire": ExerciseType.SHOULDER_PRESS,
            "row": ExerciseType.ROW,
            "rows": ExerciseType.ROW,
            "rowing": ExerciseType.ROW,
            "crunch": ExerciseType.CRUNCH,
            "crunches": ExerciseType.CRUNCH,
            "abs": ExerciseType.CRUNCH,
            "abdominaux": ExerciseType.CRUNCH,
            "deadlift": ExerciseType.DEADLIFT,
            "souleve": ExerciseType.DEADLIFT,
            "situp": ExerciseType.CRUNCH,
            "abdos": ExerciseType.CRUNCH,
            "deadlift": ExerciseType.DEADLIFT,
            "soulevé": ExerciseType.DEADLIFT,
            # Aliases for frontend IDs
            "rows": ExerciseType.ROW,
            "crunches": ExerciseType.CRUNCH,
            "tricep-dips": ExerciseType.TRICEP_DIP,
            "shoulder-press": ExerciseType.SHOULDER_PRESS,
        }
        
        pred_str = str(prediction).lower()
        return mapping.get(prediction, mapping.get(pred_str, ExerciseType.UNKNOWN))
    
    def _rule_based_classification(self, angles: Dict[str, float]) -> Tuple[ExerciseType, float]:
        """Rule-based exercise classification fallback."""
        knee_angle = (angles.get("left_knee", 180) + angles.get("right_knee", 180)) / 2
        elbow_angle = (angles.get("left_elbow", 180) + angles.get("right_elbow", 180)) / 2
        hip_angle = (angles.get("left_hip", 180) + angles.get("right_hip", 180)) / 2
        torso_angle = angles.get("torso_angle", 0)
        
        # Plank: horizontal body, arms straight
        if torso_angle > 60 and hip_angle > 150 and elbow_angle > 150:
            return ExerciseType.PLANK, 0.7
        
        # Push-up: horizontal body, arms bending
        if torso_angle > 45 and elbow_angle < 150:
            return ExerciseType.PUSHUP, 0.7
        
        # Squat: vertical torso, knees bending
        if torso_angle < 30 and knee_angle < 140:
            return ExerciseType.SQUAT, 0.7
        
        # Bicep curl: standing, elbows bending with arms close to body
        if torso_angle < 15 and elbow_angle < 120 and knee_angle > 150:
            return ExerciseType.BICEP_CURL, 0.6
        
        # Lunge: one leg forward
        left_knee = angles.get("left_knee", 180)
        right_knee = angles.get("right_knee", 180)
        if abs(left_knee - right_knee) > 30 and min(left_knee, right_knee) < 120:
            return ExerciseType.LUNGE, 0.6
        
        return ExerciseType.UNKNOWN, 0.0
    

    def update(self, angles: Dict[str, float], keypoints: Dict, exercise_type: Optional[ExerciseType] = None, visibility: float = 1.0) -> Dict[str, Any]:
        """
        Update exercise state with new frame data.
        
        Args:
            angles: Dictionary of joint angles
            keypoints: Dictionary of raw keypoints (needed for ML models)
            exercise_type: Override exercise type (or auto-detect)
            visibility: Average visibility of keypoints (0.0 to 1.0)
            
        Returns:
            Dictionary with current state and any events
        """
        current_time = time.time()
        events = []
        self.state.visibility = visibility
        
        # 1. Classify exercise if not specified
        if exercise_type is None:
            detected_exercise, confidence = self.classify_exercise(angles)
            if detected_exercise != ExerciseType.UNKNOWN:
                self.state.current_type = detected_exercise
                self.state.confidence = confidence
        else:
            # If explicit exercise provided, we strictly use it and skip detection
            # This is important to ensure the coach gives feedback for the exercise
            # the user actually selected in the UI.
            self.state.current_type = exercise_type
            self.state.confidence = 1.0
            
        # Diagnostic logging for reps
        if self.state.rep_count == 0 and len(angles) > 0 and self.state.current_type != ExerciseType.UNKNOWN:
             if int(time.time()) % 5 == 0:
                 print(f"[EXERCISE-DIAG] {self.state.current_type.value} phase: {self.state.current_phase.value}, progress: {self._rep_progress_flag}")
        
        # Detect phase and count reps based on exercise
        new_phase = self._detect_phase(angles, self.state.current_type)
        
        # Track min quality and visibility during the rep cycle
        if self._rep_progress_flag:
            self.state.min_quality_in_rep = min(self.state.min_quality_in_rep, self.state.form_quality)
            self.state.min_visibility_in_rep = min(self.state.min_visibility_in_rep, self.state.visibility)
        else:
            # Not in a rep cycle, keep trackers at current values until cycle starts
            self.state.min_quality_in_rep = self.state.form_quality
            self.state.min_visibility_in_rep = self.state.visibility
            self.state.rep_start_time = current_time

        # Check for rep completion (down -> up transition)
        rep_status, reason = self._is_rep_complete(new_phase)
        if rep_status:
            self.state.rep_count += 1
            self.state.total_reps += 1
            rep_time = current_time - self.state.last_rep_time
            self.state.last_rep_time = current_time
            
            # Track rep times for fatigue detection
            if len(self.state.rep_times) >= 5:
                self.state.rep_times.pop(0)
            self.state.rep_times.append(rep_time)
            self.state.avg_rep_time = sum(self.state.rep_times) / len(self.state.rep_times)
            
            events.append({
                "type": "rep_complete",
                "count": self.state.rep_count,
                "total_count": self.state.total_reps,
                "rep_time": round(rep_time, 2),
                "quality": round(self.state.min_quality_in_rep, 2)
            })
        elif reason:
            events.append({
                "type": "rep_rejected",
                "reason": reason
            })
        
        # Check form quality
        form_issues = self._check_form(angles, self.state.current_type)
        self.state.form_issues = form_issues
        self.state.form_quality = max(0.0, 1.0 - len(form_issues) * 0.2)
        
        if form_issues:
            events.append({
                "type": "form_warning",
                "issues": form_issues
            })

        # === ML Model Quality Check ===
        # Run primarily for pushup/squat (LSTM) or fallback to correction ONNX
        if self.state.current_type in [ExerciseType.SQUAT, ExerciseType.PUSHUP]:
            ml_label, ml_conf = self._run_lstm_quality_check(keypoints)
            if ml_label:
                self.state.ml_label = ml_label
                self.state.ml_confidence = ml_conf
                
                # If LSTM says bad form → add to feedback
                if "Incorrect" in ml_label or any(issue in ml_label.lower() for issue in ["shallow", "lean", "caving", "off", "asymmetric"]):
                    issue_code = ml_label.lower().replace(" ", "_")
                    if issue_code not in self.state.feedback_codes:
                        self.state.feedback_codes.append(issue_code)
        else:
             # === Correction ONNX for all other exercises ===
            corr_label, corr_conf = self._run_correction_onnx(keypoints)
            if corr_label:
                self.state.ml_label = corr_label
                self.state.ml_confidence = corr_conf
                issue_code = corr_label.lower().replace(" ", "_")
                if issue_code not in self.state.feedback_codes:
                    self.state.feedback_codes.append(issue_code)
        
        # Update phase
        if new_phase != self._prev_phase:
            self._phase_start_time = current_time
        self._prev_phase = new_phase
        self.state.current_phase = new_phase
        
        return {
            "exercise": self.state.current_type.value,
            "phase": self.state.current_phase.value,
            "rep_count": self.state.rep_count,
            "confidence": round(self.state.confidence, 2),
            "form_quality": round(self.state.form_quality, 2),
            "visibility": round(self.state.visibility, 2),
            "avg_rep_time": round(self.state.avg_rep_time, 2),
            "events": events,
            "ml_label": self.state.ml_label,
            "ml_confidence": self.state.ml_confidence
        }
    
    def _detect_phase(self, angles: Dict[str, float], exercise: ExerciseType) -> ExercisePhase:
        """Detect current movement phase."""
        t = self.thresholds
        
        if exercise == ExerciseType.SQUAT:
            knee_angle = min(angles.get("left_knee", 180), angles.get("right_knee", 180))
            
            if knee_angle < t.squat_knee_down + t.squat_tolerance:
                return ExercisePhase.DOWN
            elif knee_angle > t.squat_knee_up - t.squat_tolerance:
                return ExercisePhase.UP
            else:
                return ExercisePhase.TRANSITION
        
        elif exercise == ExerciseType.PUSHUP:
            elbow_angle = min(angles.get("left_elbow", 180), angles.get("right_elbow", 180))
            
            if elbow_angle < t.pushup_elbow_down + t.squat_tolerance:
                return ExercisePhase.DOWN
            elif elbow_angle > t.pushup_elbow_up - t.squat_tolerance:
                return ExercisePhase.UP
            else:
                return ExercisePhase.TRANSITION
        
        elif exercise == ExerciseType.PLANK:
            hip_angle = (angles.get("left_hip", 180) + angles.get("right_hip", 180)) / 2
            
            if t.plank_hip_min < hip_angle < t.plank_hip_max:
                return ExercisePhase.HOLD
            else:
                return ExercisePhase.IDLE
        
        elif exercise == ExerciseType.BICEP_CURL:
            elbow_angle = min(angles.get("left_elbow", 180), angles.get("right_elbow", 180))
            
            if elbow_angle < t.curl_elbow_up + 20:
                return ExercisePhase.UP
            elif elbow_angle > t.curl_elbow_down - 20:
                return ExercisePhase.DOWN
            else:
                return ExercisePhase.TRANSITION

        elif exercise == ExerciseType.TRICEP_DIP:
            elbow_angle = min(angles.get("left_elbow", 180), angles.get("right_elbow", 180))
            if elbow_angle < t.dip_elbow_down + 10:
                return ExercisePhase.DOWN
            elif elbow_angle > t.dip_elbow_up - 10:
                return ExercisePhase.UP
            else:
                return ExercisePhase.TRANSITION

        elif exercise == ExerciseType.SHOULDER_PRESS:
            elbow_angle = min(angles.get("left_elbow", 180), angles.get("right_elbow", 180))
            if elbow_angle < t.press_elbow_down + 10:
                return ExercisePhase.DOWN
            elif elbow_angle > t.press_elbow_up - 10:
                return ExercisePhase.UP
            else:
                return ExercisePhase.TRANSITION

        elif exercise == ExerciseType.ROW:
            elbow_angle = min(angles.get("left_elbow", 180), angles.get("right_elbow", 180))
            if elbow_angle < t.row_elbow_pull + 10:
                return ExercisePhase.UP  # Pulled back
            elif elbow_angle > t.row_elbow_extend - 10:
                return ExercisePhase.DOWN # Extended
            else:
                return ExercisePhase.TRANSITION

        elif exercise == ExerciseType.CRUNCH:
            hip_angle = (angles.get("left_hip", 180) + angles.get("right_hip", 180)) / 2
            if hip_angle < t.crunch_hip_up:
                return ExercisePhase.UP
            elif hip_angle > t.crunch_hip_down:
                return ExercisePhase.DOWN
            else:
                return ExercisePhase.TRANSITION

        elif exercise == ExerciseType.DEADLIFT:
            hip_angle = (angles.get("left_hip", 180) + angles.get("right_hip", 180)) / 2
            if hip_angle < t.deadlift_hip_down + 10:
                return ExercisePhase.DOWN
            elif hip_angle > t.deadlift_hip_up - 10:
                return ExercisePhase.UP
            else:
                return ExercisePhase.TRANSITION
        
        return ExercisePhase.IDLE
    
    def _is_rep_complete(self, new_phase: ExercisePhase) -> Tuple[bool, Optional[str]]:
        """Check if a rep was just completed according to strict rules."""
        current_time = time.time()
        
        rep_just_finished = False
        
        # GROUP 1: START UP -> DOWN -> UP
        if self.state.current_type in [ExerciseType.SQUAT, ExerciseType.PUSHUP, ExerciseType.TRICEP_DIP, ExerciseType.SHOULDER_PRESS]:
            if new_phase == ExercisePhase.DOWN:
                if not self._rep_progress_flag:
                    self.state.rep_start_time = current_time
                self._rep_progress_flag = True
            elif new_phase == ExercisePhase.UP and self._rep_progress_flag:
                rep_just_finished = True

        # GROUP 2: START DOWN/EXTENDED -> UP/CONTRACTED -> DOWN
        elif self.state.current_type in [ExerciseType.BICEP_CURL, ExerciseType.ROW, ExerciseType.CRUNCH, ExerciseType.DEADLIFT]:
            if new_phase == ExercisePhase.UP:
                if not self._rep_progress_flag:
                    self.state.rep_start_time = current_time
                self._rep_progress_flag = True
            elif new_phase == ExercisePhase.DOWN and self._rep_progress_flag:
                rep_just_finished = True
        
        # GROUP 3: HOLDS (Plank)
        elif self.state.current_type == ExerciseType.PLANK:
            if self._prev_phase == ExercisePhase.HOLD and new_phase != ExercisePhase.HOLD:
                duration = current_time - self._phase_start_time
                if duration > self.thresholds.plank_hold_time:
                    rep_just_finished = True

        if rep_just_finished:
            self._rep_progress_flag = False
            duration = current_time - self.state.rep_start_time
            
            # Enforce Strict Rules
            if duration < self.thresholds.min_rep_duration:
                return False, "too_fast"
            if self.state.min_visibility_in_rep < self.thresholds.min_visibility_threshold:
                return False, "low_visibility"
            if self.state.min_quality_in_rep < self.thresholds.min_form_quality_threshold:
                # Identify the specific issue for feedback
                return False, "poor_form"
            
            return True, None
            
        return False, None
    
    def _check_form(self, angles: Dict[str, float], exercise: ExerciseType) -> List[str]:
        """Check exercise form and return issues."""
        issues = []
        t = self.thresholds
        
        if exercise == ExerciseType.SQUAT:
            # Check knees tracking over toes (simplified)
            left_knee = angles.get("left_knee", 180)
            right_knee = angles.get("right_knee", 180)
            
            # Only check symmetry if actually in a squatting motion (knees significantly bent)
            # and increase threshold to 30 to account for perspective/noise
            if (left_knee < 140 or right_knee < 140) and abs(left_knee - right_knee) > 30:
                issues.append("squat_knee_uneven")
            
            torso_angle = angles.get("torso_angle", 0)
            if torso_angle > 45:
                issues.append("squat_back_round")
        
        elif exercise == ExerciseType.PUSHUP:
            hip_angle = (angles.get("left_hip", 180) + angles.get("right_hip", 180)) / 2
            
            if hip_angle < 160:
                issues.append("pushup_hips_high")
            elif hip_angle > 190:
                issues.append("pushup_hips_low")
        
        elif exercise == ExerciseType.PLANK:
            hip_angle = (angles.get("left_hip", 180) + angles.get("right_hip", 180)) / 2
            
            if hip_angle < 155:
                issues.append("plank_hips_high")
            elif hip_angle > 185:
                issues.append("plank_hips_low")
        
        elif exercise == ExerciseType.BICEP_CURL:
            # Check for swinging (indicated by shoulder angle change)
            shoulder_angle = (
                angles.get("left_shoulder", 90) + angles.get("right_shoulder", 90)
            ) / 2
            
        
            if shoulder_angle > 60:
                issues.append("curl_swing")

        elif exercise == ExerciseType.LUNGE:
            # Check for leg symmetry and depth
            left_knee = angles.get("left_knee", 180)
            right_knee = angles.get("right_knee", 180)
            
            # In a lunge, one knee should be deep
            if min(left_knee, right_knee) > 130:
                issues.append("lunge_depth")
            
            torso_angle = angles.get("torso_angle", 0)
            if torso_angle > 20:
                issues.append("lunge_torso_lean")

        elif exercise == ExerciseType.TRICEP_DIP:
            # Check for elbow flare
            left_elbow = angles.get("left_elbow", 180)
            right_elbow = angles.get("right_elbow", 180)
            
            if abs(left_elbow - right_elbow) > 20:
                issues.append("dip_uneven")

        elif exercise == ExerciseType.SHOULDER_PRESS:
            # Check for arching back
            torso_angle = angles.get("torso_angle", 0)
            if torso_angle > 20:
                issues.append("press_arch_back")

        elif exercise == ExerciseType.ROW:
            # Check for rounded back
            torso_angle = angles.get("torso_angle", 0)
            # In rowing, torso is usually tilted, but should be stable
            if torso_angle < 30:
                issues.append("row_back_round")

        elif exercise == ExerciseType.CRUNCH:
            # Check for neck strain
            torso_angle = angles.get("torso_angle", 0)
            if torso_angle > 180:
                issues.append("crunch_neck_strain")
            
            knee_angle = (angles.get("left_knee", 180) + angles.get("right_knee", 180)) / 2
            if knee_angle < 90:
                issues.append("crunch_legs_moving")

        elif exercise == ExerciseType.DEADLIFT:
             # Check for rounded back
            torso_angle = angles.get("torso_angle", 0)
            if torso_angle > 45:
                issues.append("deadlift_back_round")
        
        return issues
    
    def detect_fatigue(self) -> Tuple[bool, float]:
        """
        Detect fatigue based on rep speed slowdown.
        
        Returns:
            Tuple of (is_fatigued, slowdown_percentage)
        """
        if len(self.state.rep_times) < 3:
            return False, 0.0
        
        # Compare recent reps to initial reps
        initial_avg = sum(self.state.rep_times[:2]) / 2
        recent_avg = sum(self.state.rep_times[-2:]) / 2
        
        if initial_avg > 0:
            slowdown = ((recent_avg - initial_avg) / initial_avg) * 100
            is_fatigued = slowdown > 20
            return is_fatigued, max(0.0, slowdown)
        
        return False, 0.0
    
    def estimate_body_type(self, body_ratios: Dict[str, float]) -> Optional[str]:
        """
        Estimate body type. 
        Note: Redundant with calibration.py which uses the image-based model.
        """
        # Use simple ratio-based estimation if needed, but calibration.py handles the ONNX one.
        leg_torso = body_ratios.get("leg_torso_ratio", 1.0)
        if leg_torso > 1.15: return "athletic"
        if leg_torso < 0.85: return "fat"
        return "normal"
        return "normal"
    
    def get_intensity_adjustment(self, body_type: Optional[str]) -> Dict[str, float]:
        """
        Get workout intensity adjustments based on body type.
        
        Args:
            body_type: User's body type
            
        Returns:
            Dictionary with adjustment factors
        """
        adjustments = {
            "fat": {
                "rep_multiplier": 0.7,
                "rest_multiplier": 1.5,
                "intensity": "low",
                "focus": ["cardio", "low_impact"]
            },
            "weak": {
                "rep_multiplier": 0.8,
                "rest_multiplier": 1.3,
                "intensity": "moderate",
                "focus": ["strength", "form"]
            },
            "normal": {
                "rep_multiplier": 1.0,
                "rest_multiplier": 1.0,
                "intensity": "normal",
                "focus": ["balanced"]
            },
            "athletic": {
                "rep_multiplier": 1.2,
                "rest_multiplier": 0.8,
                "intensity": "high",
                "focus": ["endurance", "power"]
            }
        }
        
        return adjustments.get(body_type, adjustments["normal"])
    
    def apply_custom_thresholds(self, thresholds: Dict[str, float]):
        """
        Apply custom thresholds from calibration.
        
        Args:
            thresholds: Dictionary of threshold overrides
        """
        if not thresholds:
            return
            
        print(f"[EXERCISE] Applying {len(thresholds)} custom thresholds")
        
        # Mapping from frontend IDs to backend internal names
        key_mapping = {
            "squat_knee_angle": ["squat_knee_down"],
            "pushup_elbow_angle": ["pushup_elbow_down"],
            "plank_hip_angle": ["plank_hip_min", "plank_hip_max"],
            "bicep_curl_angle": ["curl_elbow_up"],
            "squat_tolerance": ["squat_tolerance"]
        }

        for key, value in thresholds.items():
            # Try mapping first
            mapped_keys = key_mapping.get(key, [key])
            for mapped_key in mapped_keys:
                if hasattr(self.thresholds, mapped_key):
                    setattr(self.thresholds, mapped_key, float(value))
                    # print(f"[EXERCISE] Updated {mapped_key} to {value}")
                else:
                    print(f"[EXERCISE] Warning: Threshold {key} (mapped as {mapped_key}) not recognized")

    def reset(self):
        """Reset exercise state for new session."""
        self.state = ExerciseState()
        self.state.total_reps = 0
        self._prev_phase = ExercisePhase.IDLE
        self._rep_progress_flag = False
        self._phase_start_time = time.time()
        print("[EXERCISE] State reset")
    
    def new_set(self):
        """Start a new set."""
        self.state.set_count += 1
        self.state.rep_count = 0
        self.state.rep_times = []
        print(f"[EXERCISE] Starting set {self.state.set_count}")
    
    def _calculate_angles(self, keypoints: Dict) -> Dict[str, float]:
        """Calculate joint angles from keypoints."""
        from pose_detector import POSE_LANDMARKS
        
        def get_point(idx):
            point = keypoints.get(POSE_LANDMARKS[idx], (0, 0, 0, 0))
            return (point[0], point[1], point[2])
        
        def calculate_angle(a, b, c):
            a, b, c = np.array(a), np.array(b), np.array(c)
            ba = a - b
            bc = c - b
            cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
            return angle
        
        angles = {}
        angles["left_elbow"] = calculate_angle(get_point(11), get_point(13), get_point(15))
        angles["right_elbow"] = calculate_angle(get_point(12), get_point(14), get_point(16))
        angles["left_shoulder"] = calculate_angle(get_point(13), get_point(11), get_point(23))
        angles["right_shoulder"] = calculate_angle(get_point(14), get_point(12), get_point(24))
        angles["left_hip"] = calculate_angle(get_point(11), get_point(23), get_point(25))
        angles["right_hip"] = calculate_angle(get_point(12), get_point(24), get_point(26))
        angles["left_knee"] = calculate_angle(get_point(23), get_point(25), get_point(27))
        angles["right_knee"] = calculate_angle(get_point(24), get_point(26), get_point(28))
        angles["left_ankle"] = calculate_angle(get_point(25), get_point(27), get_point(31))
        angles["right_ankle"] = calculate_angle(get_point(26), get_point(28), get_point(32))
        
        # Calculate torso angle (simplified)
        left_shoulder = get_point(11)
        right_shoulder = get_point(12)
        left_hip = get_point(23)
        mid_shoulder = ((left_shoulder[0] + right_shoulder[0])/2, 
                       (left_shoulder[1] + right_shoulder[1])/2, 
                       (left_shoulder[2] + right_shoulder[2])/2)
        angles["torso_angle"] = calculate_angle(mid_shoulder, left_hip, (left_hip[0], left_hip[1] - 1, left_hip[2]))
        
        return angles


# Global exercise engine instance
_exercise_engine: Optional[ExerciseEngine] = None


def get_exercise_engine() -> ExerciseEngine:
    """Get or create the global exercise engine."""
    global _exercise_engine
    if _exercise_engine is None:
        _exercise_engine = ExerciseEngine()
    return _exercise_engine


def map_exercise_name(name: str) -> ExerciseType:
    """Safely map a string name to an ExerciseType enum."""
    if not name:
        return ExerciseType.UNKNOWN
        
    name_clean = name.lower().strip().replace("-", "_")
    
    # 1. Try direct match
    try:
        return ExerciseType(name_clean)
    except ValueError:
        pass
        
    # 2. Try mapping through the engine's internal aliases
    engine = get_exercise_engine()
    # Try both original and underscore version
    result = engine._map_prediction_to_exercise(name_clean)
    if result == ExerciseType.UNKNOWN and "_" in name_clean:
        result = engine._map_prediction_to_exercise(name_clean.replace("_", "-"))
    
    return result