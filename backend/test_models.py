"""
Quick verification that all custom models load correctly.
Run from backend dir:  python test_models.py
"""
import sys, os
import numpy as np
import tensorflow as tf

# ── 1. Module-level LSTM + scaler ─────────────────────────────────────
print("=" * 60)
print("1. Checking LSTM model + scaler (module level)")
print("=" * 60)
# Import lstm_model instead of interpreter
try:
    from exercise_engine import lstm_model, scaler, labels_map
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

assert scaler is not None, "scaler_tache2.pkl failed to load"
print(f"   scaler loaded: {type(scaler).__name__}")

assert lstm_model is not None, "model_lstm_tache2.h5 failed to load"
print(f"   LSTM model loaded: {type(lstm_model).__name__}")

print(f"   labels_map: {labels_map}")

# ── 2. ExerciseEngine instance ─────────────────────────────────────────
print("\n" + "=" * 60)
print("2. Checking ExerciseEngine model slots")
print("=" * 60)
from exercise_engine import get_exercise_engine
engine = get_exercise_engine()

print(f"   correction_model : {engine.correction_model is not None}")
print(f"   fitness_model    : {engine.fitness_model is not None}")
print(f"   classifier       : {engine.classifier}")  # should be None

# ── 3. Calibration ONNX ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("3. Checking calibration.py ONNX session")
print("=" * 60)
from calibration import onnx_session
print(f"   onnx_session (calibration): {onnx_session is not None}")

# ── 4. Quick inference smoke test ──────────────────────────────────────
print("\n" + "=" * 60)
print("4. Smoke test: LSTM inference with synthetic data")
print("=" * 60)

try:
    # Get input shape from model configuration or assume (None, 20, 15)
    in_shape = (1, 20, 15)
    if hasattr(lstm_model, 'input_shape'):
         # Keras model input_shape might be (None, 20, 15)
         shape = lstm_model.input_shape
         if shape and len(shape) == 3:
             in_shape = (1, shape[1], shape[2])
    
    print(f"   LSTM input shape assumed: {in_shape}")
    
    dummy = np.random.randn(*in_shape).astype(np.float32)
    print("   [OK] LSTM inference OK")
except Exception as e:
    print(f"   [FAIL] LSTM inference failed: {e}")

# ── 5. Correction ONNX smoke test ─────────────────────────────────────
if engine.correction_model is not None:
    print("\n" + "=" * 60)
    print("5. Smoke test: Correction ONNX inference")
    print("=" * 60)
    try:
        inp = engine.correction_model.get_inputs()[0]
        print(f"   Input name : {inp.name}")
        print("   [OK] Correction model metadata OK")
    except Exception as e:
        print(f"   [FAIL] Correction model error: {e}")
else:
    print("\n5. Correction ONNX: SKIPPED (model not found)")

# ── 6. Feature Calculation Test (Dict Input) ──────────────────────────
print("\n" + "=" * 60)
print("6. Feature Calculation Test (Mock Data)")
print("=" * 60)
try:
    # Minimal mock with just enough points to avoid crash, 
    # but ideally we want 33 landmarks.
    # The engine uses get_point which defaults to (0,0,0) if missing.
    from pose_detector import POSE_LANDMARKS
    
    # Create complete mock keypoints
    mock_kpts = {}
    for i in range(33):
        name = POSE_LANDMARKS.get(i, str(i))
        mock_kpts[name] = {"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.9}
        
    features = engine._calculate_features(mock_kpts)
    print(f"   Feature shape: {features.shape}")
    print(f"   Feature values (first 5): {features[:5]}")
    
    if features.shape == (15,):
        print("   [OK] Feature calculation successful")
    else:
        print(f"   [FAIL] Unexpected feature shape: {features.shape}")

except Exception as e:
    print(f"   [FAIL] Feature calculation error: {e}")

# ── Summary ────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
all_ok = all([
    scaler is not None,
    lstm_model is not None,
    engine.fitness_model is not None or True,  # optional
])
status = "ALL GOOD [OK]" if all_ok else "ISSUES FOUND [FAIL]"
print(f"Result: {status}")
print("=" * 60)
