import cv2
import numpy as np
import onnxruntime as ort

# === CONFIGURATION ===
CALIB_FILE = "stereo_calibration.npz"
MODEL_PATH = "hitnet_middlebury_480x640.onnx" # Make sure to download this!
WIDTH, HEIGHT = 640, 480 

class HitNetRunner:
    def __init__(self, model_path):
        self.session = ort.InferenceSession(model_path, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.input_names = [input.name for input in self.session.get_inputs()]
        self.output_names = [output.name for output in self.session.get_outputs()]
        
        # Get model expected input shape (usually matches your 640x480, but good to check)
        self.input_shape = self.session.get_inputs()[0].shape
        self.net_h, self.net_w = self.input_shape[2], self.input_shape[3]

    def compute(self, left_img, right_img):
        # 1. Prepare Images
        # HitNet usually expects RGB, float32, normalized, and specific dimensions
        imgL = cv2.cvtColor(left_img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        imgR = cv2.cvtColor(right_img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

        # Resize if model differs from capture (though your config matches)
        if (imgL.shape[1], imgL.shape[0]) != (self.net_w, self.net_h):
            imgL = cv2.resize(imgL, (self.net_w, self.net_h))
            imgR = cv2.resize(imgR, (self.net_w, self.net_h))

        # Transpose to (Batch, Channel, Height, Width)
        blobL = np.transpose(imgL, (2, 0, 1))[None, :, :, :]
        blobR = np.transpose(imgR, (2, 0, 1))[None, :, :, :]

        # 2. Inference
        outputs = self.session.run(self.output_names, {
            self.input_names[0]: blobL,
            self.input_names[1]: blobR
        })

        # 3. Process Output (Disparity Map)
        disparity = outputs[0].squeeze()
        
        # If we resized inputs, we might need to scale disparity back (omitted for 1:1 match)
        return disparity

def gstreamer_pipeline(sensor_id=0, width=640, height=480, framerate=30):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width={width}, height={height}, format=NV12, framerate={framerate}/1 ! "
        f"nvvidconv ! video/x-raw, format=BGRx ! "
        "videoconvert ! video/x-raw, format=BGR ! appsink drop=1"
    )

def run_depth_sensing():
    # Load calibration data
    try:
        data = np.load(CALIB_FILE)
        mtxL, distL = data['mtxL'], data['distL']
        mtxR, distR = data['mtxR'], data['distR']
        R, T = data['R'], data['T']
    except Exception as e:
        print(f"Error loading calibration file: {e}")
        return

    # Stereo Rectification
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        mtxL, distL, mtxR, distR, (WIDTH, HEIGHT), R, T, alpha=0
    )
    map1_L, map2_L = cv2.initUndistortRectifyMap(mtxL, distL, R1, P1, (WIDTH, HEIGHT), cv2.CV_16SC2)
    map1_R, map2_R = cv2.initUndistortRectifyMap(mtxR, distR, R2, P2, (WIDTH, HEIGHT), cv2.CV_16SC2)

    # === INIT NEURAL NET ===
    try:
        print("Loading Neural Network...")
        stereo_net = HitNetRunner(MODEL_PATH)
        print("Model Loaded!")
    except Exception as e:
        print(f"Failed to load ONNX model: {e}")
        print("Make sure 'hitnet_middlebury_480x640.onnx' is in the folder.")
        return

    cap_left = cv2.VideoCapture(gstreamer_pipeline(sensor_id=0, width=WIDTH, height=HEIGHT), cv2.CAP_GSTREAMER)
    cap_right = cv2.VideoCapture(gstreamer_pipeline(sensor_id=1, width=WIDTH, height=HEIGHT), cv2.CAP_GSTREAMER)

    while True:
        retL, frameL = cap_left.read()
        retR, frameR = cap_right.read()

        if not retL or not retR: break

        # 1. Rectify (CRITICAL: Neural nets still need rectified inputs!)
        rectified_L = cv2.remap(frameL, map1_L, map2_L, cv2.INTER_LINEAR)
        rectified_R = cv2.remap(frameR, map1_R, map2_R, cv2.INTER_LINEAR)

        # 2. Neural Inference
        disparity = stereo_net.compute(rectified_L, rectified_R)

        # 3. Visualization
        # Normalize disparity for display (HitNet output is metric-like, needs scaling)
        disp_vis = (disparity / np.max(disparity) * 255).astype(np.uint8)
        disp_color = cv2.applyColorMap(disp_vis, cv2.COLORMAP_MAGMA)

        cv2.imshow("Left Rectified", rectified_L)
        cv2.imshow("Neural Depth", disp_color)

        if cv2.waitKey(1) == ord('q'):
            break

    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_depth_sensing()