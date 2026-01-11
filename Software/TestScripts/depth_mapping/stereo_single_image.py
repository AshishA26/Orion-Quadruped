import cv2
import numpy as np
import onnxruntime as ort
import os
import requests
import sys

# === CONFIGURATION ===
# We use a smaller model version (240x320) for decent CPU speed. 
# It will resize your images to this, compute depth, and resize back.
MODEL_URL = "https://github.com/ibaiGorordo/ONNX-CREStereo-Depth-Estimation/raw/main/models/crestereo_combined_iter2_240x320.onnx"
MODEL_PATH = "./models/crestereo_combined_iter2_360x640.onnx"

# Input Resolution for the model (Must match the model file downloaded)
INPUT_H, INPUT_W = 360, 640

def download_model(url, path):
    if not os.path.exists(path):
        print(f"Model not found. Downloading from {url}...")
        response = requests.get(url, stream=True)
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    else:
        print(f"Model found at {path}")

def preprocess(img, w, h):
    # Resize to the specific dimensions required for this input layer
    img_resized = cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    # Transpose to (C, H, W) and normalize
    img_blob = np.transpose(img_rgb, (2, 0, 1)).astype(np.float32) / 255.0
    return np.expand_dims(img_blob, axis=0)

def main(left_image_path, right_image_path):
    # 1. Setup
    download_model(MODEL_URL, MODEL_PATH)
    
    # Check for images
    if not os.path.exists(left_image_path) or not os.path.exists(right_image_path):
        print("Error: Input images not found!")
        return

    print("Loading Neural Network (this may take a moment)...")
    # 'CPUExecutionProvider' is default. It will automatically use GPU if 'onnxruntime-gpu' is installed
    session = ort.InferenceSession(MODEL_PATH, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    
    # Get input names (usually 'left' and 'right')
    input_names = [node.name for node in session.get_inputs()]
    output_names = [node.name for node in session.get_outputs()]

    # 2. Read Images
    imgL_orig = cv2.imread(left_image_path)
    imgR_orig = cv2.imread(right_image_path)
    original_h, original_w = imgL_orig.shape[:2]

    # Prepare Dual-Resolution Inputs
    # Init: Half-size (320x180) | Next: Full-size (640x360)
    blobL_init = preprocess(imgL_orig, INPUT_W // 2, INPUT_H // 2)
    blobR_init = preprocess(imgR_orig, INPUT_W // 2, INPUT_H // 2)
    blobL_next = preprocess(imgL_orig, INPUT_W, INPUT_H)
    blobR_next = preprocess(imgR_orig, INPUT_W, INPUT_H)

    print(f"Running Inference (Input: {INPUT_W}x{INPUT_H})...")
    
    # Matching the specific keys for the 'combined' 640x360 ONNX export
    input_feed = {
        'init_left': blobL_init,
        'init_right': blobR_init,
        'next_left': blobL_next,
        'next_right': blobR_next
    }
    
    try:
        outputs = session.run(output_names, input_feed)
    except Exception as e:
        print(f"Inference failed: {e}")
        # Debug: Print what the model actually wants
        print("Model Inputs required:", [inp.name for inp in session.get_inputs()])
        return
    
    # 5. Post-Process
    # The output is disparity (pixel shift). 
    flow_up = outputs[0] # Shape is usually (1, 2, H, W) or (1, H, W) depending on export
    
    # Squeeze to get (H, W) or (2, H, W)
    disparity = np.squeeze(flow_up)
    
    # If 2 channels (flow_x, flow_y), take the first one (x-axis disparity)
    if len(disparity.shape) == 3:
        disparity = disparity[0, :, :]

    # Resize result back to original resolution
    disparity_resized = cv2.resize(disparity, (original_w, original_h))

    # 6. Visualization
    # Normalize to 0-255 for viewing
    norm_disp = cv2.normalize(disparity_resized, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    color_map = cv2.applyColorMap(norm_disp, cv2.COLORMAP_MAGMA)

    # Show/Save
    concat = np.hstack((imgL_orig, color_map))
    cv2.imshow("Original | Neural Disparity", concat)
    cv2.imwrite("output_disparity.png", color_map)
    print("Result saved to output_disparity.png")
    
    print("Press any key to exit...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_stereo.py im0.png im1.png")
    else:
        main(sys.argv[1], sys.argv[2])