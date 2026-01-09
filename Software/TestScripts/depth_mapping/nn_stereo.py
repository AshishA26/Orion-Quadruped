import cv2
import numpy as np
import onnxruntime as ort

# === CONFIGURATION ===
# Model Path: Download CREStereo or RAFT-Stereo ONNX model
# Recommended: CREStereo_init_iter2_120x160.onnx for speed
MODEL_PATH = "models/crestereo_combined_iter2_120x160.onnx" 

CALIB_FILE = "stereo_calibration.npz"
WIDTH, HEIGHT = 640, 360
INPUT_WIDTH, INPUT_HEIGHT = 480, 320 # Model input size (smaller = faster)

def gstreamer_pipeline(sensor_id=0, width=WIDTH, height=HEIGHT, framerate=30):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width={width}, height={height}, format=NV12, framerate={framerate}/1 ! "
        "nvvidconv ! video/x-raw, format=BGRx ! "
        "videoconvert ! video/x-raw, format=BGR ! appsink drop=1"
    )

class NeuralStereoMatcher:
    def __init__(self, model_path):
        # Initialize ONNX Runtime with CUDA (GPU)
        providers = [
            ('CUDAExecutionProvider', {
                'device_id': 0,
                'arena_extend_strategy': 'kNextPowerOfTwo',
                'cudnn_conv_algo_search': 'EXHAUSTIVE',
                'do_copy_in_default_stream': True,
            }),
            'CPUExecutionProvider',
        ]
        self.session = ort.InferenceSession(model_path, providers=providers)
        
        # Get input name (usually 'left' and 'right' or 'images')
        self.input_names = [node.name for node in self.session.get_inputs()]
        self.output_names = [node.name for node in self.session.get_outputs()]
        
    def compute(self, left_img, right_img):
        # 1. Preprocess
        # Resize to model input size
        h, w = left_img.shape[:2]
        l_resized = cv2.resize(left_img, (INPUT_WIDTH, INPUT_HEIGHT))
        r_resized = cv2.resize(right_img, (INPUT_WIDTH, INPUT_HEIGHT))
        
        # Normalize and Transpose (HWC -> CHW)
        # CREStereo/RAFT usually expect normalization specific to their training
        # Here we use standard ImageNet mean/std as a generic placeholder or simple 0-255 scaling
        l_blob = self._preprocess(l_resized)
        r_blob = self._preprocess(r_resized)
        
        # 2. Inference
        # Some models take concatenated images, others take separate
        if len(self.input_names) == 2:
            inputs = {self.input_names[0]: l_blob, self.input_names[1]: r_blob}
        else:
            # Concatenate along channel dimension if model expects single input
            inputs = {self.input_names[0]: np.concatenate((l_blob, r_blob), axis=1)}
            
        output = self.session.run(self.output_names, inputs)
        
        # 3. Post-process
        # Disparity is usually the first output
        disp = output[0]
        
        # Squeeze batch/channel dims and resize back to original resolution
        disp = np.squeeze(disp)
        disp_resized = cv2.resize(disp, (w, h))
        
        return disp_resized

    def _preprocess(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        # Add batch dimension and channel first: (1, 3, H, W)
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)
        return img

def run_depth_sensing():
    # Load calibration data
    try:
        data = np.load(CALIB_FILE)
        mtxL, distL = data['mtxL'], data['distL']
        mtxR, distR = data['mtxR'], data['distR']
        R, T = data['R'], data['T']
    except Exception as e:
        print(f"Error loading calibration: {e}\nUsing Dummy Calibration.")
        # Dummy values to prevent crash if file missing
        mtxL = mtxR = np.eye(3)
        distL = distR = np.zeros(5)
        R, T = np.eye(3), np.zeros((3,1))
        # return # Uncomment to force exit

    # Rectification Maps
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        mtxL, distL, mtxR, distR, (WIDTH, HEIGHT), R, T, alpha=0
    )
    map1_L, map2_L = cv2.initUndistortRectifyMap(mtxL, distL, R1, P1, (WIDTH, HEIGHT), cv2.CV_32FC1)
    map1_R, map2_R = cv2.initUndistortRectifyMap(mtxR, distR, R2, P2, (WIDTH, HEIGHT), cv2.CV_32FC1)

    # Initialize Neural Network
    print(f"Loading Neural Network from {MODEL_PATH}...")
    try:
        matcher = NeuralStereoMatcher(MODEL_PATH)
        print("Model loaded successfully on GPU.")
    except Exception as e:
        print(f"Failed to load ONNX model: {e}")
        return

    cap_left = cv2.VideoCapture(gstreamer_pipeline(sensor_id=0), cv2.CAP_GSTREAMER)
    cap_right = cv2.VideoCapture(gstreamer_pipeline(sensor_id=1), cv2.CAP_GSTREAMER)

    while True:
        retL, frameL = cap_left.read()
        retR, frameR = cap_right.read()

        if not retL or not retR: break

        # 1. Rectify images
        rectified_L = cv2.remap(frameL, map1_L, map2_L, cv2.INTER_LINEAR)
        rectified_R = cv2.remap(frameR, map1_R, map2_R, cv2.INTER_LINEAR)

        # 2. Neural Disparity Inference
        # Unlike SGBM, we feed color images usually
        disparity = matcher.compute(rectified_L, rectified_R)

        # 3. Visualization
        # Normalize disparity to 0-255 for colormap
        disp_vis = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        disp_color = cv2.applyColorMap(disp_vis, cv2.COLORMAP_MAGMA)

        cv2.imshow("Left Rectified", rectified_L)
        cv2.imshow("Neural Disparity", disp_color)

        if cv2.waitKey(1) == ord('q'):
            break

    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_depth_sensing()