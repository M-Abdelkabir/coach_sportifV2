import onnxruntime as ort
import sys
from pathlib import Path

def inspect_model(model_path, log_file):
    log_file.write(f"\nInspecting {model_path}...\n")
    try:
        session = ort.InferenceSession(model_path)
        log_file.write("\nInputs:\n")
        for i in session.get_inputs():
            log_file.write(f"  Name: {i.name}, Shape: {i.shape}, Type: {i.type}\n")
        log_file.write("\nOutputs:\n")
        for o in session.get_outputs():
            log_file.write(f"  Name: {o.name}, Shape: {o.shape}, Type: {o.type}\n")
    except Exception as e:
        log_file.write(f"Error: {e}\n")

if __name__ == "__main__":
    with open("onnx_info.txt", "w") as f:
        models_dir = Path("backend/models")
        for model_file in models_dir.glob("*.onnx"):
            inspect_model(str(model_file), f)
    print("Done. Results in onnx_info.txt")
