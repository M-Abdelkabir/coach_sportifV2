import tensorflow as tf
from pathlib import Path
import numpy as np

# Paths
MODELS_DIR = Path("c:/Users/Gato/Downloads/coach_sportif-main/coach_sportif-main/backend/models")
SRC_MODEL_PATH = MODELS_DIR / "model_lstm_tache2.h5"
DEST_TFLITE_PATH = MODELS_DIR / "model_lstm_tache2_optimized.tflite"

def create_unrolled_model(original_model):
    """Recreate the model architecture with unroll=True for LSTMs."""
    
    # We know the architecture from inspection:
    # Input(20, 15) -> LSTM(64, ret_seq=True) -> Dropout -> LSTM(32) -> Dropout -> Dense(32) -> Dense(8)
    
    inputs = tf.keras.Input(shape=(20, 15))
    
    # Layer 1: LSTM 64, return_sequences=True
    x = tf.keras.layers.LSTM(64, return_sequences=True, unroll=True, name="lstm_unrolled_1")(inputs)
    x = tf.keras.layers.Dropout(0.2)(x)
    
    # Layer 2: LSTM 32, return_sequences=False
    x = tf.keras.layers.LSTM(32, return_sequences=False, unroll=True, name="lstm_unrolled_2")(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    
    # Layer 3: Dense 32 Relu
    x = tf.keras.layers.Dense(32, activation='relu', name="dense_1")(x)
    
    # Layer 4: Dense 8 Softmax
    outputs = tf.keras.layers.Dense(8, activation='softmax', name="dense_out")(x)
    
    new_model = tf.keras.Model(inputs, outputs)
    new_model.build(input_shape=(None, 20, 15))
    return new_model

def transfer_weights(src_model, dest_model):
    """Transfer weights layer by layer."""
    src_layers = [l for l in src_model.layers if len(l.weights) > 0]
    dest_layers = [l for l in dest_model.layers if len(l.weights) > 0]
    
    if len(src_layers) != len(dest_layers):
        print(f"Warning: Layer count mismatch! Src: {len(src_layers)}, Dest: {len(dest_layers)}")
        return False
        
    for i, (src, dest) in enumerate(zip(src_layers, dest_layers)):
        print(f"Transferring weights: {src.name} -> {dest.name}")
        dest.set_weights(src.get_weights())
        
    return True

def main():
    try:
        # 1. Load Original
        print(f"Loading original model from {SRC_MODEL_PATH}...")
        original_model = tf.keras.models.load_model(str(SRC_MODEL_PATH))
        
        # 2. Create Unrolled
        print("Creating unrolled model...")
        unrolled_model = create_unrolled_model(original_model)
        
        # 3. Transfer Weights
        print("Transferring weights...")
        if not transfer_weights(original_model, unrolled_model):
            print("Weight transfer failed.")
            return
            
        # 4. Convert to TFLite
        print("Converting to TFLite...")
        converter = tf.lite.TFLiteConverter.from_keras_model(unrolled_model)
        
        # Enable standard optimizations
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Ensure only standard ops are used (NO FLEX)
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
        
        tflite_model = converter.convert()
        
        # 5. Save
        with open(DEST_TFLITE_PATH, "wb") as f:
            f.write(tflite_model)
            
        print(f"Success! Optimized TFLite model saved to: {DEST_TFLITE_PATH}")
        print("This model should run on Raspberry Pi 5 with standard TFLite runtime.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
