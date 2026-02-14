"""
T-Pose calibration module.
Collects keypoints during T-pose and calculates body ratios + personalized thresholds.
"""
import asyncio
import time
from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path  # Fixed import

import numpy as np
import cv2

from pose_detector import get_pose_detector

# Load ONNX model safely
MODELS_DIR = Path(__file__).parent / "models"
onnx_path = MODELS_DIR / "fitness_model.onnx"
onnx_session = None

if onnx_path.exists():
    try:
        import onnxruntime as ort
        onnx_session = ort.InferenceSession(str(onnx_path))
        print(f"[CALIBRATION] Loaded ONNX model from {onnx_path}")
    except Exception as e:
        print(f"[CALIBRATION] Failed to load ONNX model: {e}")
else:
    print(f"[CALIBRATION] ONNX model not found at {onnx_path}")


@dataclass
class CalibrationConfig:
    """Configuration for calibration process."""
    duration_seconds: float = 5.0
    sample_rate_hz: float = 10.0  # Samples per second
    stability_threshold: float = 0.02  # Maximum movement for stability
    min_visibility: float = 0.7  # Minimum landmark visibility


class Calibrator:
    """
    T-Pose calibration handler.
    Collects keypoints and calculates body measurements.
    """
    
    def __init__(self, config: Optional[CalibrationConfig] = None):
        """Initialize calibrator with config."""
        self.config = config or CalibrationConfig()
        self.samples: List[Dict] = []
        self.is_calibrating = False
        self.progress = 0.0
        self.status = "idle"
        
    async def calibrate_stream(self, pose_detector=None) -> AsyncGenerator[Dict, None]:
        """
        Run calibration process as an async generator.
        Yields progress updates and finally the result.
        
        Args:
            pose_detector: Optional pose detector instance
            
        Yields:
            Dict with progress or result
        """
        if pose_detector is None:
            pose_detector = get_pose_detector()
        
        self.samples = []
        self.is_calibrating = True
        self.status = "starting"
        self.progress = 0.0
        
        yield {"type": "progress", "progress": self.progress, "status": self.status}
        
        # Calculate number of samples to collect
        total_samples = int(self.config.duration_seconds * self.config.sample_rate_hz)
        sample_interval = 1.0 / self.config.sample_rate_hz
        
        print(f"[CALIBRATION] Starting - collecting {total_samples} samples over {self.config.duration_seconds}s")
        
        start_time = time.time()
        collected = 0
        last_frame = None
        
        try:
            while collected < total_samples and self.is_calibrating:
                # Use faster polling but only collect at sample_rate
                await asyncio.sleep(0.01)
                
                # Check if it's time for a sample
                if time.time() - start_time < (collected * sample_interval):
                    continue
                
                success, frame = pose_detector.get_frame()
                if not success or frame is None:
                    continue
                
                last_frame = frame  # Store for body type classification
                
                # Detect pose (non-blocking if using dedicated worker)
                pose_data = pose_detector.latest_result
                
                if pose_data and self._check_visibility(pose_data["keypoints"]):
                    self.samples.append(pose_data)
                    collected += 1
                    self.progress = collected / total_samples
                    self.status = "collecting"
                    
                    yield {
                        "type": "progress", 
                        "progress": self.progress, 
                        "status": self.status,
                        "collected": collected,
                        "total": total_samples
                    }
            
            elapsed = time.time() - start_time
            print(f"[CALIBRATION] Collected {len(self.samples)} samples in {elapsed:.1f}s")
            
        except Exception as e:
            self.is_calibrating = False
            self.status = "error"
            yield {
                "type": "result",
                "success": False,
                "message": f"Erreur de calibration: {str(e)}",
                "ratios": None,
                "thresholds": None,
                "body_type": None
            }
            return
        
        self.is_calibrating = False
        
        if len(self.samples) < total_samples * 0.5: # 50% threshold for success
            self.status = "failed"
            yield {
                "type": "result",
                "success": False,
                "message": f"Pas assez de données ({len(self.samples)}/{total_samples}). Reculez un peu.",
                "ratios": None,
                "thresholds": None,
                "body_type": None
            }
            return
        
        # Check stability
        stability = self._check_stability()
        if stability > self.config.stability_threshold * 2.5: # Relaxed slightly for home use
            self.status = "unstable"
            yield {
                "type": "result",
                "success": False,
                "message": "Restez immobile ! Trop de mouvements détectés.",
                "ratios": None,
                "thresholds": None,
                "body_type": None
            }
            return
        
        # Calculate ratios
        ratios = self._calculate_ratios()
        if not ratios:
            self.status = "failed"
            yield {
                "type": "result",
                "success": False,
                "message": "Échec du calcul des proportions corporelles",
                "ratios": None,
                "thresholds": None,
                "body_type": None
            }
            return
        
        # Generate personalized thresholds
        thresholds = self._generate_thresholds(ratios)
        
        # Classify body type from last frame
        body_type = "unknown"
        if last_frame is not None and onnx_session is not None:
            body_type = self._classify_body_type(last_frame)
        
        self.status = "complete"
        self.progress = 1.0
        
        print(f"[CALIBRATION] Complete - Ratios: {ratios}, Body type: {body_type}")
        
        yield {
            "type": "result",
            "success": True,
            "message": "Calibration terminée. Vos seuils sont appliqués.",
            "ratios": ratios,
            "thresholds": thresholds,
            "body_type": body_type,
            "samples_collected": len(self.samples),
            "stability_score": round(1.0 - min(stability / 0.1, 1.0), 2)
        }
    
    async def calibrate(self, duration: Optional[float] = None) -> Dict:
        """Perform calibration asynchronously (simplified version)."""
        from pose_detector import get_pose_detector
        
        pose_detector = get_pose_detector()
        config_duration = duration or self.config.duration_seconds
        sample_interval = 1.0 / self.config.sample_rate_hz
        total_samples = int(config_duration * self.config.sample_rate_hz)
        
        self.samples = []
        self.is_calibrating = True
        last_frame = None
        
        # Collect samples
        for _ in range(total_samples):
            if not self.is_calibrating:
                break
                
            success, frame = pose_detector.get_frame()
            if success:
                last_frame = frame
                pose_data = pose_detector.detect_pose(frame)
                if pose_data and self._check_visibility(pose_data["keypoints"]):
                    self.samples.append(pose_data)
            
            await asyncio.sleep(sample_interval)
        
        self.is_calibrating = False
        
        if len(self.samples) < total_samples * 0.6:
            return {
                "success": False,
                "message": f"Insufficient samples: {len(self.samples)}. Make sure you're visible.",
                "body_type": None
            }
        
        ratios = self._calculate_ratios()
        if not ratios:
            return {
                "success": False,
                "message": "Failed to calculate body ratios",
                "body_type": None
            }
        
        thresholds = self._generate_thresholds(ratios)
        
        # Classify body type
        body_type = "unknown"
        if last_frame is not None and onnx_session is not None:
            body_type = self._classify_body_type(last_frame)
        
        return {
            "success": True,
            "message": "Calibration complete",
            "ratios": ratios,
            "thresholds": thresholds,
            "body_type": body_type
        }
    
    def _check_visibility(self, keypoints: Dict) -> bool:
        """Check if key landmarks are visible enough."""
        required = [
            "left_shoulder", "right_shoulder",
            "left_hip", "right_hip",
            "left_knee", "right_knee"
        ]
        
        for name in required:
            if name not in keypoints:
                return False
            if keypoints[name].get("visibility", 0) < self.config.min_visibility:
                return False
        
        return True
    
    def _check_stability(self) -> float:
        """Calculate movement/stability during calibration."""
        if len(self.samples) < 2:
            return 1.0
        
        # Compare first and last samples
        movements = []
        
        for name in ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]:
            positions = [
                (s["keypoints"][name]["normalized"]["x"], 
                 s["keypoints"][name]["normalized"]["y"])
                for s in self.samples if name in s["keypoints"]
            ]
            
            if len(positions) > 1:
                # Calculate standard deviation of positions
                x_std = np.std([p[0] for p in positions])
                y_std = np.std([p[1] for p in positions])
                movements.append(x_std + y_std)
        
        return np.mean(movements) if movements else 1.0
    
    def _calculate_ratios(self) -> Optional[Dict[str, float]]:
        """Calculate average body ratios from collected samples."""
        if not self.samples:
            return None
        
        pose_detector = get_pose_detector()
        all_ratios = []
        
        for sample in self.samples:
            ratios = pose_detector.calculate_body_ratios(sample["keypoints"])
            if ratios:
                all_ratios.append(ratios)
        
        if not all_ratios:
            return None
        
        # Average all ratio measurements
        avg_ratios = {}
        for key in all_ratios[0].keys():
            values = [r[key] for r in all_ratios if key in r]
            if values:
                avg_ratios[key] = round(np.mean(values), 4)
        
        return avg_ratios
    
    def _generate_thresholds(self, ratios: Dict[str, float]) -> Dict[str, float]:
        """
        Generate personalized exercise thresholds based on body ratios.
        
        Args:
            ratios: Body measurement ratios
            
        Returns:
            Dictionary of threshold adjustments
        """
        # Base thresholds (standard values)
        thresholds = {
            "squat_knee_angle": 90.0,
            "squat_tolerance": 10.0,
            "pushup_elbow_angle": 90.0,
            "plank_hip_angle": 170.0,
            "bicep_curl_angle": 45.0,
        }
        
        # Adjust based on leg/torso ratio
        leg_torso = ratios.get("leg_torso_ratio", 1.0)
        
        # Longer legs = need more knee flexion for proper squat depth
        if leg_torso > 1.1:
            thresholds["squat_knee_angle"] = 85.0
            thresholds["squat_tolerance"] = 12.0
        elif leg_torso < 0.9:
            thresholds["squat_knee_angle"] = 95.0
            thresholds["squat_tolerance"] = 8.0
        
        # Adjust based on shoulder width
        shoulder_width = ratios.get("shoulder_width", 0.3)
        
        # Wider shoulders might need different pushup arm position
        if shoulder_width > 0.35:
            thresholds["pushup_elbow_angle"] = 85.0
        
        # Arm length affects bicep curl range
        arm_length = ratios.get("arm_length", 0.2)
        if arm_length > 0.25:
            thresholds["bicep_curl_angle"] = 50.0
        
        return thresholds
    
    def _classify_body_type(self, frame: np.ndarray) -> str:
        """Classify body type using the vision-only ONNX model."""
        if frame is None or onnx_session is None:
            return "unknown"
        
        try:
            # Preprocess image (BGR → RGB, resize, normalize)
            if frame is None:
                return "unknown"
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame.shape[2] == 3 else frame            
            resized = cv2.resize(frame_rgb, (224, 224))
            normalized = resized.astype(np.float32) / 255.0
            # CHW format + batch dimension
            input_data = np.expand_dims(np.transpose(normalized, (2, 0, 1)), axis=0)  # shape (1, 3, 224, 224)

            # Run inference
            input_name = onnx_session.get_inputs()[0].name  # should be "pixel_values"
            embedding = onnx_session.run(None, {input_name: input_data})[0]  # (1, 512)

            # Optional: L2 normalize (recommended for cosine similarity)
            embedding_norm = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)

            # =============================================
            # Body type classification logic
            # Option 1: Simple threshold-based (fast, no extra model)
            # Example: use some hand-crafted features from embedding or norm magnitude
            norm_value = np.linalg.norm(embedding)
            if norm_value > 12.0:
                return "athletic"
            elif norm_value > 9.0:
                return "normal"
            elif norm_value > 6.0:
                return "weak"
            else:
                return "fat"

            # Option 2: Better – cosine similarity with reference embeddings
            # (You need to pre-compute these reference vectors once)
            #
            # reference_embeddings = np.array([
            #     fat_emb,      # shape (512,)
            #     weak_emb,
            #     normal_emb,
            #     athletic_emb
            # ])  # shape (4, 512)
            #
            # similarities = np.dot(embedding_norm, reference_embeddings.T)[0]
            # predicted_idx = np.argmax(similarities)
            # body_types = ['fat', 'weak', 'normal', 'athletic']
            # return body_types[predicted_idx]

        except Exception as e:
            print(f"[CALIBRATION] Body type classification error: {e}")
            return "unknown"
        
    def cancel(self):
        """Cancel ongoing calibration."""
        self.is_calibrating = False
        self.status = "cancelled"
        print("[CALIBRATION] Cancelled")
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current calibration progress."""
        return {
            "is_calibrating": self.is_calibrating,
            "progress": round(self.progress, 2),
            "status": self.status,
            "samples_collected": len(self.samples)
        }


# Synchronous version for REST endpoint
async def run_calibration_async(duration: int = 5) -> Dict[str, Any]:
    """Helper to run calibration asynchronously and return the final result."""
    calibrator = Calibrator(CalibrationConfig(duration_seconds=float(duration)))
    return await calibrator.calibrate(duration=float(duration))


# Global calibrator instance
_calibrator: Optional[Calibrator] = None


def get_calibrator() -> Calibrator:
    """Get or create the global calibrator instance."""
    global _calibrator
    if _calibrator is None:
        _calibrator = Calibrator()
    return _calibrator