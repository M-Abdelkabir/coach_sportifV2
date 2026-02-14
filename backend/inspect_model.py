import tensorflow as tf
from pathlib import Path
import json

MODELS_DIR = Path("c:/Users/Gato/Downloads/coach_sportif-main/coach_sportif-main/backend/models")
model_path = MODELS_DIR / "model_lstm_tache2.h5"

try:
    model = tf.keras.models.load_model(str(model_path))
    print(f"Loaded model from {model_path}")
    model.summary()
    
    config = model.get_config()
    print("\nModel Config:")
    print(json.dumps(config, indent=2))
    
    # Check layers for LSTM
    has_lstm = False
    for layer in model.layers:
        if "LSTM" in layer.__class__.__name__:
            print(f"Found LSTM layer: {layer.name}")
            print(f"  unroll: {layer.get_config().get('unroll')}")
            has_lstm = True
            
except Exception as e:
    print(f"Error loading model: {e}")
