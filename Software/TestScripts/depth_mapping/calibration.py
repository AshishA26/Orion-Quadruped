import cv2
import numpy as np
import os
import time

# === CONFIGURATION ===
CHESSBOARD_SIZE = (9, 6)  # Inner corners
SQUARE_SIZE = 0.025       # Meters
SAVE_DIR = "calibration_images"
CALIB_FILE = "stereo_calibration.npz"

# === FIXED PIPELINE ===
# We use 1920x1080 @ 30fps because your logs confirmed this mode exists.
# We then downscale to 640x360 for the display window to keep it fast.
def gstreamer_pipeline(sensor_id=0, capture_width=1920, capture_height=1080, display_width=640, display_height=360, framerate=30, flip_method=0):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width=(int){capture_width}, height=(int){capture_height}, format=(string)NV12, framerate=(fraction){framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width=(int){display_width}, height=(int){display_height}, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
    )

def calibrate_stereo():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # 1. Open Cameras
    print("Opening Camera 0 (Left)...")
    cap_left = cv2.VideoCapture(gstreamer_pipeline(sensor_id=0), cv2.CAP_GSTREAMER)
    
    print("Opening Camera 1 (Right)...")
    cap_right = cv2.VideoCapture(gstreamer_pipeline(sensor_id=1), cv2.CAP_GSTREAMER)

    # 2. Strict Check
    if not cap_left.isOpened() or not cap_right.isOpened():
        print("\nERROR: Could not open cameras!")
        print("Check: Did you run 'sudo systemctl restart nvargus-daemon'?")
        return

    print("\nCameras Opened Successfully!")
    print("Controls:\n  'c': Capture frame\n  'q': Finish & Calibrate")

    # Calibration Setup
    objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
    objp *= SQUARE_SIZE

    objpoints = [] 
    imgpoints_left = []
    imgpoints_right = []
    count = 0

    while True:
        retL, frameL = cap_left.read()
        retR, frameR = cap_right.read()

        if not retL or not retR:
            print("Dropped frame...")
            continue

        # Show images side by side
        vis = np.hstack((frameL, frameR))
        cv2.imshow('Stereo Calibration', vis)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            # Find corners
            grayL = cv2.cvtColor(frameL, cv2.COLOR_BGR2GRAY)
            grayR = cv2.cvtColor(frameR, cv2.COLOR_BGR2GRAY)
            ret1, corners1 = cv2.findChessboardCorners(grayL, CHESSBOARD_SIZE, None)
            ret2, corners2 = cv2.findChessboardCorners(grayR, CHESSBOARD_SIZE, None)

            if ret1 and ret2:
                # Refine and Save
                term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners1 = cv2.cornerSubPix(grayL, corners1, (11,11), (-1,-1), term)
                corners2 = cv2.cornerSubPix(grayR, corners2, (11,11), (-1,-1), term)
                
                imgpoints_left.append(corners1)
                imgpoints_right.append(corners2)
                objpoints.append(objp)
                
                # Save raw frames
                cv2.imwrite(f"{SAVE_DIR}/left_{count}.png", frameL)
                cv2.imwrite(f"{SAVE_DIR}/right_{count}.png", frameR)
                print(f"Captured pair {count+1}")
                count += 1
                
                # Visual feedback (invert colors briefly)
                cv2.imshow('Stereo Calibration', 255-vis)
                cv2.waitKey(100)
            else:
                print("Chessboard not found in both cameras. Try adjusting angle/lighting.")

        elif key == ord('q'):
            break

    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

    if count < 10:
        print("Not enough images (need >10). Exiting.")
        return

    print("Calibrating... This takes ~30 seconds...")
    
    # Run Calibration
    img_shape = frameL.shape[:2][::-1]
    
    # Individual
    retL, mtxL, distL, _, _ = cv2.calibrateCamera(objpoints, imgpoints_left, img_shape, None, None)
    retR, mtxR, distR, _, _ = cv2.calibrateCamera(objpoints, imgpoints_right, img_shape, None, None)
    
    # Stereo
    flags = cv2.CALIB_FIX_INTRINSIC
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)
    retS, mtxL, distL, mtxR, distR, R, T, E, F = cv2.stereoCalibrate(
        objpoints, imgpoints_left, imgpoints_right,
        mtxL, distL, mtxR, distR, img_shape,
        criteria=criteria, flags=flags
    )

    print(f"Stereo RMS Error: {retS}")
    np.savez(CALIB_FILE, mtxL=mtxL, distL=distL, mtxR=mtxR, distR=distR, R=R, T=T)
    print(f"Saved to {CALIB_FILE}")

if __name__ == "__main__":
    calibrate_stereo()