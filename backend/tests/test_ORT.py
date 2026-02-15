# test_ORT.py
import onnxruntime as ort
import numpy as np

model_path = r"models\fitness_model.onnx"

print(f"Loading model from: {model_path}")

try:
    sess = ort.InferenceSession(model_path)
    print("\nSUCCESS: Model loaded!")

    # Show model signature
    print("\nInputs:")
    for inp in sess.get_inputs():
        print(f"  - Name: {inp.name:20}   Expected shape: {inp.shape}")

    print("\nOutputs:")
    for out in sess.get_outputs():
        print(f"  - Name: {out.name:20}   Expected shape: {out.shape}")

    # Dummy input matching CLIP: batch=1, channels=3, height=224, width=224
    dummy_input = np.random.randn(1, 3, 224, 224).astype(np.float32)

    # Run inference
    input_name = sess.get_inputs()[0].name   # usually "pixel_values"
    outputs = sess.run(None, {input_name: dummy_input})
    embedding = outputs[0]

    print("\nInference successful!")
    print(f"Output shape: {embedding.shape}")
    print(f"Sample values (first 8): {embedding[0][:8]}")
    print(f"Norm of embedding: {np.linalg.norm(embedding):.4f}  (should be around 1 if normalized)")

except Exception as e:
    print("\nERROR during load or inference:")
    print(str(e))