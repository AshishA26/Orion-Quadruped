import cv2
import numpy as np
import onnxruntime as ort
import os
import requests

# === CONFIGURATION ===
# Using MiDaS v2.1 Small (256x256 input)
MODEL_URL = "https://github.com/onnx/models/raw/main/vision/depth_estimation/midas/model/midas-9.onnx"
MODEL_PATH = "./models/midas_v21_small_256.onnx"

def download_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading MiDaS ONNX model...")
        r = requests.get(MODEL_URL, stream=True)
        with open(MODEL_PATH, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")

def main(image_path):
    download_model()
    
    # Load Model
    # Use ['CUDAExecutionProvider'] for Jetson/Desktop GPU
    session = ort.InferenceSession(MODEL_PATH, providers=['CPUExecutionProvider'])
    input_name = session.get_inputs()[0].name

    # Load and Preprocess Image
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Image not found.")
        return
        
    img_h, img_w = img.shape[:2]
    
    # 1. Resize and convert to RGB
    img_input = cv2.resize(img, (256, 256))
    img_input = cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB)

    # 2. Normalize and explicitly cast to FLOAT32
    # This is the line that fixes the "double vs float" error
    img_input = img_input.astype(np.float32) / 255.0

    # 3. Apply Mean/Std normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_input = (img_input - mean) / std

    # 4. Final formatting
    img_input = np.transpose(img_input, (2, 0, 1)) # HWC to CHW
    img_input = np.expand_dims(img_input, axis=0)  # Add batch dimension

    # Inference
    print("Computing depth...")
    output = session.run(None, {input_name: img_input})
    depth = np.squeeze(output[0])

    # Post-process: Resize back to original resolution
    depth_resized = cv2.resize(depth, (img_w, img_h))
    
    # Normalize for visualization
    depth_min = depth_resized.min()
    depth_max = depth_resized.max()
    depth_norm = (255 * (depth_resized - depth_min) / (depth_max - depth_min)).astype(np.uint8)
    depth_color = cv2.applyColorMap(depth_norm, cv2.COLORMAP_JET)

    # Show result
    cv2.imshow("Original", img)
    cv2.imshow("MiDaS Depth", depth_color)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run_midas.py image.jpg")
    else:
        main(sys.argv[1])