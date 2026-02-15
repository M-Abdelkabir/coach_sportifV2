"""
Pose detection using MediaPipe Tasks API (0.10.30+).
Extracts keypoints from webcam feed for exercise analysis.
"""
import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
import time
import math
import urllib.request
import os
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from hardware_manager import get_hardware_manager

# MediaPipe Tasks imports
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# Model file paths
MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "pose_landmarker_full.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
YOLO_MODEL_PATH = MODEL_DIR / "unified_model.pt"


# MediaPipe pose landmark indices (same as legacy API)
POSE_LANDMARKS = {
    0: "nose",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",
    29: "left_heel",
    30: "right_heel",
    31: "left_foot_index",
    32: "right_foot_index",
}


def download_model():
    """Download the pose landmarker model if not present or corrupt."""
    import zipfile
    
    # Check if exists and is valid
    if MODEL_PATH.exists():
        try:
            # MediaPipe task files are zip archives
            with zipfile.ZipFile(MODEL_PATH) as z:
                 if z.testzip() is None:
                     print(f"[POSE] Model exists and is valid at {MODEL_PATH}")
                     return True
        except zipfile.BadZipFile:
            print(f"[POSE] Model at {MODEL_PATH} is corrupt. Retying download...")
            try:
                os.remove(MODEL_PATH)
            except OSError as e:
                print(f"[POSE] Error removing corrupt model: {e}")
                return False

    try:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[POSE] Downloading pose model from {MODEL_URL}...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        
        # Verify download
        if MODEL_PATH.exists():
            try:
                 with zipfile.ZipFile(MODEL_PATH) as z:
                     if z.testzip() is None:
                         print(f"[POSE] Model downloaded to {MODEL_PATH}")
                         return True
            except zipfile.BadZipFile:
                print("[POSE] Downloaded model is corrupt.")
                return False
                
        return False
    except Exception as e:
        print(f"[POSE] Failed to download model: {e}")
        return False


class PoseDetector:
    """
    Pose detection using MediaPipe Tasks API.
    Extracts 33 body landmarks and calculates joint angles.
    """
    
    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        use_yolo: bool = False
    ):
        """
        Initialize the pose detector.
        
        Args:
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
        """
        self.landmarker = None
        self.yolo_model = None
        self.latest_result = None
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        
        # Enable YOLO if requested
        self.use_yolo = use_yolo
        self.yolo_failed_permanently = False
        if self.use_yolo:
            print("[POSE] YOLO mode enabled. Loading model...")
            self._load_yolo_model()
        else:
            print("[POSE] Using MediaPipe for pose detection")

        # Initialize MediaPipe (either as primary or backup)
        if True: # Always attempt to load MediaPipe for fallback
            # Download model if needed
            if not download_model():
                print("[POSE] Warning: Pose detection will not work without model")
                # return # Don't return, YOLO might work

            # Create pose landmarker
            try:
                base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
                options = vision.PoseLandmarkerOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.IMAGE,
                    min_pose_detection_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence,
                    output_segmentation_masks=False
                )
                self.landmarker = vision.PoseLandmarker.create_from_options(options)
                print("[POSE] MediaPipe Pose detector initialized (Tasks API)")
            except Exception as e:
                print(f"[POSE] Failed to initialize pose detector: {e}")
                
                # Attempt to recover if it's a file issue
                if "Unable to open zip archive" in str(e) or "packet" in str(e):
                    print("[POSE] Model file likely corrupt. Deleting and retrying...")
                    try:
                         if MODEL_PATH.exists():
                             os.remove(MODEL_PATH)
                         if download_model():
                             # Retry initialization once
                             try:
                                 self.landmarker = vision.PoseLandmarker.create_from_options(options)
                                 print("[POSE] MediaPipe Pose detector initialized after recovery")
                             except Exception as retry_e:
                                  print(f"[POSE] Recovery failed: {retry_e}")
                                  self.landmarker = None
                    except Exception as cleanup_e:
                         print(f"[POSE] Cleanup failed: {cleanup_e}") 
                
                if self.landmarker is None:
                    print("[POSE] Critical: MediaPipe could not be initialized.")
        
        # Camera state
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.frame_count = 0
        self.fps = 0.0
        self.last_fps_time = time.time()
        self.fps_frame_count = 0
        
        # Threading and caching
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._capture_thread: Optional[threading.Thread] = None
        self.camera_id = 0  # Default to 0, will be updated by start_camera
        
        # Dedicated worker thread for pose detection
        self._processing_queue = queue.Queue(maxsize=1)
        self._result_id = 0
        self._detector_active = True # Lifecycle for the worker thread
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

        # Centering state
        self.current_pan_angle = 0
        self.pan_sensitivity = 45.0  # Degrees of pan per 1.0 of normalized offset
        self.pan_threshold = 0.1     # Only move if offset > 10% from center

    def _load_yolo_model(self):
        """Load YOLO model for pose detection."""
        try:
            from ultralytics import YOLO
            
            # 1. Try unified model path
            if YOLO_MODEL_PATH.exists():
                print(f"[POSE] Loading YOLO model from {YOLO_MODEL_PATH}...")
                self.yolo_model = YOLO(str(YOLO_MODEL_PATH))
            else:
                # 2. Fallback to nano model (will auto-download)
                print(f"[POSE] Unified model not found. Using {MODEL_DIR / 'yolov8n-pose.pt'}...")
                self.yolo_model = YOLO(str(MODEL_DIR / "yolov8n-pose.pt"))
                
            print("[POSE] YOLO model loaded successfully")
        except ImportError:
            print("[POSE] Error: 'ultralytics' library not installed. Falling back to MediaPipe.")
            self.use_yolo = False
        except Exception as e:
            print(f"[POSE] Failed to load YOLO model: {e}")
            self.use_yolo = False
    
    def start_camera(self, camera_id: int = 0, width: int = 640, height: int = 480) -> bool:
        """
        Start webcam capture.
        """

        # 1. Check if already running with this ID and cap is valid
        if self.is_running and getattr(self, 'camera_id', -1) == camera_id:
            if self.cap and self.cap.isOpened():
                return True
        
        # 2. Prevent concurrent start attempts or ensure clean state
        self.is_running = False
        self._stop_event.set()
        
        # Wait for previous capture thread to finish completely
        if self._capture_thread and threading.current_thread() != self._capture_thread:
            self._capture_thread.join(timeout=1.0)
            self._capture_thread = None
        
        # Release existing capture object explicitly
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

        # Reset state for new capture
        self.camera_id = camera_id
        self._stop_event.clear()
        with self._frame_lock:
            self._latest_frame = None # Clear cache
            self.fps_frame_count = 0
        
        try:
            print(f"[POSE] Attempting to start camera {camera_id}...")
            # ... rest of logic
            
            # Simple list of backends to try
            backends = [cv2.CAP_DSHOW, cv2.CAP_ANY, cv2.CAP_MSMF]
            
            for backend in backends:
                backend_name = "DEFAULT" if backend == cv2.CAP_ANY else ("DSHOW" if backend == cv2.CAP_DSHOW else "MSMF")
                print(f"[POSE] Trying {backend_name} backend...")
                self.cap = cv2.VideoCapture(camera_id, backend)
                
                if self.cap.isOpened():
                    # Set resolution
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    
                    # IMPORTANT: Verify we can actually read from this camera
                    success = False
                    for attempt in range(10):
                        ret, test_frame = self.cap.read()
                        if ret and test_frame is not None and test_frame.size > 0:
                            success = True
                            break
                        time.sleep(0.1)
                    
                    if success:
                        print(f"[POSE] Camera {camera_id} started successfully with {backend_name}. Starting capture thread.")
                        self.is_running = True
                        self._stop_event.clear()
                        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
                        self._capture_thread.start()
                        return True
                    else:
                        print(f"[POSE] {backend_name} opened but failed to read frames. Releasing...")
                        self.cap.release()
                        self.cap = None
                else:
                    if self.cap:
                        self.cap.release()
                        self.cap = None
            
            print(f"[POSE] CRITICAL: All backends failed for camera {camera_id}")
            return False
            
        except Exception as e:
            print(f"[POSE] Camera error: {e}")
            return False
            
    def _capture_loop(self):
        """Background thread to capture frames continuously."""
        print("[POSE] Capture loop started")
        consecutive_failures = 0
        while not self._stop_event.is_set():
            if self.cap:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    consecutive_failures = 0
                    with self._frame_lock:
                        self._latest_frame = frame
                    
                    # Update FPS
                    self.fps_frame_count += 1
                    current_time = time.time()
                    if current_time - self.last_fps_time >= 1.0:
                        self.fps = self.fps_frame_count / (current_time - self.last_fps_time)
                        self.fps_frame_count = 0
                        self.last_fps_time = current_time

                    # Push to inference worker if it's empty (don't backlog)
                    if self._processing_queue.empty():
                        try:
                            self._processing_queue.put_nowait(frame)
                        except queue.Full:
                            pass
                else:
                    consecutive_failures += 1
                    if consecutive_failures % 30 == 0:
                        print(f"[POSE] Warning: {consecutive_failures} consecutive frame read failures")
                    
                    if consecutive_failures >= 150:
                        print(f"[POSE] Too many failures on camera {self.camera_id}. Attempting auto-detection...")
                        current_fail_id = self.camera_id
                        self.is_running = False # Mark as not running to stop other calls
                        
                        # Try other indices first, then the current one as last resort
                        indices_to_try = [0, 1, 2]
                        if current_fail_id in indices_to_try:
                            indices_to_try.remove(current_fail_id)
                            indices_to_try.append(current_fail_id) # Move failing index to end
                        
                        found = False
                        for next_id in indices_to_try:
                            print(f"[POSE] Probing camera index {next_id}...")
                            if self.start_camera(next_id):
                                found = True
                                break
                        
                        if not found:
                            print("[POSE] CRITICAL: Could not find any working camera.")
                            self.is_running = False
                        
                        consecutive_failures = 0
                        break # Exit current thread loop
            else:
                print("[POSE] Capture loop: cap is None, exiting")
                break
        print("[POSE] Capture loop stopped")
    
    def stop_camera(self):
        """Stop webcam capture."""
        print("[POSE] Stopping camera...")
        self.is_running = False
        self._stop_event.set()
        
        if self._capture_thread:
            if threading.current_thread() != self._capture_thread:
                self._capture_thread.join(timeout=2.0)
            self._capture_thread = None
            
        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                print(f"[POSE] Error releasing camera: {e}")
            self.cap = None
        print("[POSE] Camera stopped and resources released")
    
    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Get the latest frame from the cache.
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_running:
            return False, None
            
        with self._frame_lock:
            if self._latest_frame is not None:
                return True, self._latest_frame.copy()
            
        return False, None
    
    def _worker_loop(self):
        """Dedicated background thread for AI inference."""
        print("[POSE] Inference worker thread started")
        while self._detector_active:
            try:
                # Get the latest frame from the queue, wait for a bit
                frame = self._processing_queue.get(timeout=1.0)
                if frame is None:
                    continue
                
                # Perform inference
                res = self.detect_pose(frame)
                if res:
                    self._result_id += 1
                    res["result_id"] = self._result_id
                    with self._frame_lock:
                        self.latest_result = res
                
                self._processing_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[POSE] Worker error: {e}")
                time.sleep(0.1)
        print("[POSE] Inference worker thread stopped")


    def detect_pose(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Detect pose in a frame.
        """
        # Debug: Check frame quality
        if self.frame_count % 30 == 0:
            h, w = frame.shape[:2]
            brightness = np.mean(frame)
            print(f"[POSE] Processing frame: {w}x{h}, Brightness: {brightness:.1f}")
            if brightness < 30:
                print("[POSE] WARNING: Image is very dark!")

        # Flip frame for correct L/R identification (Front camera assumption)
        processing_frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        if self.use_yolo and self.yolo_model:
            result = self._detect_yolo(processing_frame)
            if result:
                if self.frame_count % 30 == 0:
                    print(f"[POSE] YOLO detection successful (conf: {self.min_detection_confidence})")
                
                # Flip coordinates back to match the original frame (for frontend display)
                self._flip_result_coordinates(result, w)
                
                self.latest_result = result
                return result
            
            if self.frame_count % 30 == 0:
                print("[POSE] YOLO failed, falling back to MediaPipe...")
        
        result = self._detect_mediapipe(processing_frame)
        if result:
            # Flip coordinates back for MediaPipe too
            self._flip_result_coordinates(result, w)
            self.latest_result = result
            
            # Auto-centering logic
            self._update_auto_centering(result)

        return result

    def _update_auto_centering(self, result: Dict[str, Any]):
        """
        Calculate user offset from center and adjust camera pan.
        """
        if not result or "keypoints" not in result:
            return

        # Calculate average X position of main torso points
        torso_points = ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]
        x_coords = []
        for p in torso_points:
            if p in result["keypoints"] and result["keypoints"][p].get("visibility", 0) > 0.5:
                x_coords.append(result["keypoints"][p]["normalized"]["x"])
        
        if not x_coords:
            return

        avg_x = sum(x_coords) / len(x_coords)
        offset = avg_x - 0.5  # 0 is center, -0.5 is left, 0.5 is right
        
        # Only adjust if beyond threshold
        if abs(offset) > self.pan_threshold:
            # Simple proportional adjustment
            # Note: We subtract because if user is to the right (offset > 0), 
            # we need to rotate camera to the right (negative or positive depending on mounting)
            # Assuming positive pan = right
            adjustment = offset * self.pan_sensitivity * 0.1 # Small step
            self.current_pan_angle = max(-90, min(90, self.current_pan_angle + adjustment))
            
            get_hardware_manager().set_camera_pan(self.current_pan_angle)
            if self.frame_count % 30 == 0:
                print(f"[POSE] Auto-centering: user at {avg_x:.2f}, pan set to {self.current_pan_angle:.1f}°")
        # elif self.frame_count % 30 == 0:
        #      print("[POSE] MediaPipe also failed to detect body")
             
        #      # DEBUG: Debugging why detection fails
        #      # 1. Try simple face detection to see if ANY person is there
        #      try:
        #          gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #          face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        #          faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        #          if len(faces) > 0:
        #              print(f"[POSE] DEBUG: OpenCV detected {len(faces)} face(s), but Pose models failed.")
        #          else:
        #              print("[POSE] DEBUG: OpenCV also found NO faces.")
        #      except Exception as e:
        #          print(f"[POSE] DEBUG: Could not run face check: {e}")


        return result

    def _flip_result_coordinates(self, result: Dict[str, Any], width: int):
        """
        Flip x-coordinates of detection results to match the original (unflipped) frame.
        Used when we flip the input frame for detection to ensure correct L/R identification.
        """
        if not result or "keypoints" not in result:
            return

        for name, kpt in result["keypoints"].items():
            # Flip absolute X (0..width -> width..0)
            kpt["x"] = width - kpt["x"]
            
            # Flip normalized X (0..1 -> 1..0)
            if "normalized" in kpt:
                kpt["normalized"]["x"] = 1.0 - kpt["normalized"]["x"]

    def _detect_yolo(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """YOLOv11-pose detection implementation."""
        try:
            # Use the configured confidence threshold
            results = self.yolo_model(frame, verbose=False, conf=getattr(self, 'min_detection_confidence', 0.25))
            if not results or len(results[0].keypoints) == 0:
                return None
        except AttributeError as e:
            if "'Conv' object has no attribute 'bn'" in str(e):
                # Critical fix for YOLOv8/v11 on some CPU envs
                print("[POSE] Suppression error detected (fusion bug). Disabling YOLO for this session.")
                self.yolo_failed_permanently = True
                self.use_yolo = False
                return None
            raise e
        except Exception as e:
            print(f"[POSE] YOLO detection error: {e}")
            # If it's a model-internal error, we might want to fallback permanently too
            if "model" in str(e).lower() or "forward" in str(e).lower():
                self.yolo_failed_permanently = True
                self.use_yolo = False
            return None
        
        self.frame_count += 1
        h, w = frame.shape[:2]
        keypoints = {}
        
        # YOLO keypoints format: [N, 17, 3] (x, y, conf)
        # Mapping YOLO indices to our POSE_LANDMARKS names
        # YOLOv8/v11 pose indices: 0:nose, 5:l_shoulder, 6:r_shoulder, 7:l_elbow, 8:r_elbow, 
        # 9:l_wrist, 10:r_wrist, 11:l_hip, 12:r_hip, 13:l_knee, 14:r_knee, 15:l_ankle, 16:r_ankle
        yolo_map = {
            0: "nose", 5: "left_shoulder", 6: "right_shoulder", 7: "left_elbow", 
            8: "right_elbow", 9: "left_wrist", 10: "right_wrist", 11: "left_hip", 
            12: "right_hip", 13: "left_knee", 14: "right_knee", 15: "left_ankle", 16: "right_ankle"
        }
        
        kpts = results[0].keypoints.data[0].cpu().numpy() # [17, 3]
        
        for idx, name in yolo_map.items():
            x, y, conf = kpts[idx]
            keypoints[name] = {
                "x": float(x),
                "y": float(y),
                "z": 0.0,
                "visibility": float(conf),
                "normalized": {"x": float(x/w), "y": float(y/h), "z": 0.0}
            }
            
        angles = self._calculate_angles(keypoints)
        return {
            "keypoints": keypoints,
            "angles": angles,
            "frame_id": self.frame_count,
            "fps": round(self.fps, 1),
            "timestamp": time.time(),
            "model": "yolo"
        }

    def _detect_mediapipe(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """MediaPipe detection implementation."""
        if self.landmarker is None:
            return None

        h_orig, w_orig = frame.shape[:2]
        
        # MediaPipe Tasks API prefers square images to avoid "NORM_RECT" warnings 
        # and coordinate projection issues on some platforms.
        size = max(h_orig, w_orig)
        pad_h = (size - h_orig) // 2
        pad_w = (size - w_orig) // 2
        
        # Pad to square
        padded_frame = cv2.copyMakeBorder(
            frame, pad_h, size - h_orig - pad_h, 
            pad_w, size - w_orig - pad_w, 
            cv2.BORDER_CONSTANT, value=[0, 0, 0]
        )
        
        rgb_frame = cv2.cvtColor(padded_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        try:
            result = self.landmarker.detect(mp_image)
        except Exception as e:
            print(f"[POSE] MediaPipe detection error: {e}")
            return None
        
        if not result.pose_landmarks or len(result.pose_landmarks) == 0:
            return None
        
        # Landmarks processing
        self.frame_count += 1
        keypoints = {}
        landmarks = result.pose_landmarks[0]
        
        for idx, name in POSE_LANDMARKS.items():
            if idx < len(landmarks):
                landmark = landmarks[idx]
                # Map back to original (non-padded) coordinates
                # landmark.x/y are 0..1 in the padded (square) image
                x_px = landmark.x * size
                y_px = landmark.y * size
                
                # Subtract padding
                x_orig = x_px - pad_w
                y_orig = y_px - pad_h
                
                keypoints[name] = {
                    "x": x_orig,
                    "y": y_orig,
                    "z": landmark.z,
                    "visibility": landmark.visibility if hasattr(landmark, 'visibility') else 1.0,
                    "normalized": {
                        "x": x_orig / w_orig, 
                        "y": y_orig / h_orig, 
                        "z": landmark.z
                    }
                }
        
        angles = self._calculate_angles(keypoints)
        return {
            "keypoints": keypoints,
            "angles": angles,
            "frame_id": self.frame_count,
            "fps": round(self.fps, 1),
            "timestamp": time.time(),
            "model": "mediapipe"
        }
    
    def _calculate_angles(self, keypoints: Dict) -> Dict[str, float]:
        """
        Calculate joint angles from keypoints.
        
        Args:
            keypoints: Dictionary of keypoint positions
            
        Returns:
            Dictionary of angle names to values in degrees
        """
        angles = {}
        
        try:
            # Left elbow angle (shoulder-elbow-wrist)
            angles["left_elbow"] = self._calculate_angle(
                keypoints["left_shoulder"],
                keypoints["left_elbow"],
                keypoints["left_wrist"]
            )
            
            # Right elbow angle
            angles["right_elbow"] = self._calculate_angle(
                keypoints["right_shoulder"],
                keypoints["right_elbow"],
                keypoints["right_wrist"]
            )
            
            # Left knee angle (hip-knee-ankle)
            angles["left_knee"] = self._calculate_angle(
                keypoints["left_hip"],
                keypoints["left_knee"],
                keypoints["left_ankle"]
            )
            
            # Right knee angle
            angles["right_knee"] = self._calculate_angle(
                keypoints["right_hip"],
                keypoints["right_knee"],
                keypoints["right_ankle"]
            )
            
            # Left hip angle (shoulder-hip-knee)
            angles["left_hip"] = self._calculate_angle(
                keypoints["left_shoulder"],
                keypoints["left_hip"],
                keypoints["left_knee"]
            )
            
            # Right hip angle
            angles["right_hip"] = self._calculate_angle(
                keypoints["right_shoulder"],
                keypoints["right_hip"],
                keypoints["right_knee"]
            )
            
            # Left shoulder angle (elbow-shoulder-hip)
            angles["left_shoulder"] = self._calculate_angle(
                keypoints["left_elbow"],
                keypoints["left_shoulder"],
                keypoints["left_hip"]
            )
            
            # Right shoulder angle
            angles["right_shoulder"] = self._calculate_angle(
                keypoints["right_elbow"],
                keypoints["right_shoulder"],
                keypoints["right_hip"]
            )
            
            # Torso angle (vertical alignment)
            angles["torso_angle"] = self._calculate_torso_angle(keypoints)
            
        except (KeyError, TypeError) as e:
            print(f"[POSE] Angle calculation error: {e}")
        
        return angles
    
    def _calculate_angle(self, p1: Dict, p2: Dict, p3: Dict) -> float:
        """
        Calculate angle between three points.
        
        Args:
            p1: First point (e.g., shoulder)
            p2: Vertex point (e.g., elbow)
            p3: Third point (e.g., wrist)
            
        Returns:
            Angle in degrees
        """
        # Get coordinates
        a = np.array([p1["x"], p1["y"]])
        b = np.array([p2["x"], p2["y"]])
        c = np.array([p3["x"], p3["y"]])
        
        # Calculate vectors
        ba = a - b
        bc = c - b
        
        # Calculate angle using dot product
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        return math.degrees(angle)
    
    def _calculate_torso_angle(self, keypoints: Dict) -> float:
        """Calculate torso angle from vertical."""
        try:
            # Midpoint of shoulders
            mid_shoulder = (
                (keypoints["left_shoulder"]["x"] + keypoints["right_shoulder"]["x"]) / 2,
                (keypoints["left_shoulder"]["y"] + keypoints["right_shoulder"]["y"]) / 2
            )
            
            # Midpoint of hips
            mid_hip = (
                (keypoints["left_hip"]["x"] + keypoints["right_hip"]["x"]) / 2,
                (keypoints["left_hip"]["y"] + keypoints["right_hip"]["y"]) / 2
            )
            
            # Calculate angle from vertical
            dx = mid_shoulder[0] - mid_hip[0]
            dy = mid_shoulder[1] - mid_hip[1]
            
            angle = math.degrees(math.atan2(abs(dx), abs(dy)))
            return angle
            
        except Exception:
            return 0.0
    
    def draw_pose(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw pose landmarks on frame using the unified result dictionary.
        
        Args:
            frame: BGR image
            
        Returns:
            Frame with pose overlay
        """
        if self.latest_result is None or "keypoints" not in self.latest_result:
            return frame
        
        annotated_frame = frame.copy()
        keypoints = self.latest_result["keypoints"]
        h, w = frame.shape[:2]
        
        # 1. Draw joints
        for name, kpt in keypoints.items():
            if kpt.get("visibility", 0) > 0.3:
                x = int(kpt["x"])
                y = int(kpt["y"])
                cv2.circle(annotated_frame, (x, y), 5, (0, 255, 0), -1)
                cv2.putText(annotated_frame, name.split('_')[-1], (x+5, y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # 2. Draw connections (skeleton)
        connections = [
            ("left_shoulder", "right_shoulder"),
            ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
            ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"),
            ("left_shoulder", "left_hip"), ("right_shoulder", "right_hip"),
            ("left_hip", "right_hip"),
            ("left_hip", "left_knee"), ("left_knee", "left_ankle"),
            ("right_hip", "right_knee"), ("right_knee", "right_ankle")
        ]
        
        for start_name, end_name in connections:
            if start_name in keypoints and end_name in keypoints:
                start = keypoints[start_name]
                end = keypoints[end_name]
                if start.get("visibility", 0) > 0.3 and end.get("visibility", 0) > 0.3:
                    p1 = (int(start["x"]), int(start["y"]))
                    p2 = (int(end["x"]), int(end["y"]))
                    cv2.line(annotated_frame, p1, p2, (0, 255, 0), 2)
        
        return annotated_frame
    
    def calculate_body_ratios(self, keypoints: Dict) -> Dict[str, float]:
        """
        Calculate body ratios for calibration.
        
        Args:
            keypoints: Dictionary of keypoint positions
            
        Returns:
            Dictionary of body ratios
        """
        try:
            # Shoulder width (normalized by frame width)
            shoulder_width = abs(
                keypoints["left_shoulder"]["normalized"]["x"] -
                keypoints["right_shoulder"]["normalized"]["x"]
            )
            
            # Arm length (shoulder to wrist)
            left_arm = self._distance(
                keypoints["left_shoulder"], keypoints["left_wrist"]
            )
            right_arm = self._distance(
                keypoints["right_shoulder"], keypoints["right_wrist"]
            )
            arm_length = (left_arm + right_arm) / 2
            
            # Leg length (hip to ankle)
            left_leg = self._distance(
                keypoints["left_hip"], keypoints["left_ankle"]
            )
            right_leg = self._distance(
                keypoints["right_hip"], keypoints["right_ankle"]
            )
            leg_length = (left_leg + right_leg) / 2
            
            # Torso height (shoulder to hip)
            left_torso = self._distance(
                keypoints["left_shoulder"], keypoints["left_hip"]
            )
            right_torso = self._distance(
                keypoints["right_shoulder"], keypoints["right_hip"]
            )
            torso_height = (left_torso + right_torso) / 2
            
            # Leg to torso ratio
            leg_torso_ratio = leg_length / (torso_height + 1e-6)
            
            return {
                "shoulder_width": round(shoulder_width, 4),
                "arm_length": round(arm_length, 4),
                "leg_length": round(leg_length, 4),
                "torso_height": round(torso_height, 4),
                "leg_torso_ratio": round(leg_torso_ratio, 4)
            }
            
        except Exception as e:
            print(f"[POSE] Error calculating body ratios: {e}")
            return {}
    
    def _distance(self, p1: Dict, p2: Dict) -> float:
        """Calculate Euclidean distance between two points (normalized coords)."""
        dx = p1["normalized"]["x"] - p2["normalized"]["x"]
        dy = p1["normalized"]["y"] - p2["normalized"]["y"]
        return math.sqrt(dx**2 + dy**2)
    
    def is_camera_available(self) -> bool:
        """Check if camera is available without intrusive probing."""
        # If it's already running, it's definitely available
        if self.is_running and self.cap and self.cap.isOpened():
            return True
        
        # On Raspberry/Linux, we might check /dev/video0 existence
        # On Windows, we prefer to rely on the last known state or is_running 
        # to avoid driver hangs caused by frequent cv2.VideoCapture(0) probes.
        return self.is_running
    
    def cleanup(self):
        """Clean up resources."""
        self._detector_active = False # Stop the worker thread
        self.stop_camera()
        if self.landmarker is not None:
            self.landmarker.close()
        print("[POSE] Pose detector cleaned up")


# Global pose detector instance
_pose_detector: Optional[PoseDetector] = None


def get_pose_detector() -> PoseDetector:
    """Get or create the global pose detector."""
    global _pose_detector
    if _pose_detector is None:
        import os
        use_yolo = os.getenv("USE_YOLO", "true").lower() == "true"
        _pose_detector = PoseDetector(use_yolo=use_yolo)
    return _pose_detector
