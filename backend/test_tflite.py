import tensorflow as tf
import numpy as np
import os

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "model_lstm_tache2_optimized.tflite")

def test_tflite_model():
    print(f"Testing TFLite model: {MODEL_PATH}")
    
    if not os.path.exists(MODEL_PATH):
        print(f"[FAIL] Model not found: {MODEL_PATH}")
        return

    try:
        # Load the TFLite model and allocate tensors.
        interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()

        # Get input and output tensors.
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        print(f"Input details: {input_details[0]['shape']}")
        print(f"Output details: {output_details[0]['shape']}")

        # Test model on random input data.
        input_shape = input_details[0]['shape']
        input_data = np.array(np.random.random_sample(input_shape), dtype=np.float32)
        interpreter.set_tensor(input_details[0]['index'], input_data)

        interpreter.invoke()

        # The function `get_tensor()` returns a copy of the tensor data.
        # Use `tensor()` in order to get a pointer to the tensor.
        output_data = interpreter.get_tensor(output_details[0]['index'])
        print(f"Inference output: {output_data}")
        
        if output_data.shape == (1, 8):
            print("[OK] TFLite model inference successful. Output shape matches (1, 8).")
        else:
            print(f"[FAIL] Unexpected output shape: {output_data.shape}")
            
    except Exception as e:
        print(f"[FAIL] Error testing TFLite model: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tflite_model()
