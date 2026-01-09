import cv2
import numpy as np

# === CONFIGURATION ===
CALIB_FILE = "stereo_calibration.npz"
# Lower resolution for SGBM performance
WIDTH, HEIGHT = 640, 360

def gstreamer_pipeline(sensor_id=0, width=WIDTH, height=HEIGHT, framerate=30):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width={width}, height={height}, format=NV12, framerate={framerate}/1 ! "
        "nvvidconv ! video/x-raw, format=BGRx ! "
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
        print("Please run the calibration script first!")
        return

    # Stereo Rectification
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        mtxL, distL, mtxR, distR, (WIDTH, HEIGHT), R, T, alpha=0
    )

    map1_L, map2_L = cv2.initUndistortRectifyMap(mtxL, distL, R1, P1, (WIDTH, HEIGHT), cv2.CV_16SC2)
    map1_R, map2_R = cv2.initUndistortRectifyMap(mtxR, distR, R2, P2, (WIDTH, HEIGHT), cv2.CV_16SC2)

    # Setup Stereo SGBM
    # Tuning these parameters is key for your specific environment
    min_disp = 0
    num_disp = 16 * 6  # Must be divisible by 16
    stereo = cv2.StereoSGBM_create(
        minDisparity=min_disp,
        numDisparities=num_disp,
        blockSize=5,
        P1=8 * 3 * 5**2,
        P2=32 * 3 * 5**2,
        disp12MaxDiff=1,
        uniquenessRatio=10,
        speckleWindowSize=100,
        speckleRange=32
    )

    cap_left = cv2.VideoCapture(gstreamer_pipeline(sensor_id=0, width=WIDTH, height=HEIGHT), cv2.CAP_GSTREAMER)
    cap_right = cv2.VideoCapture(gstreamer_pipeline(sensor_id=1, width=WIDTH, height=HEIGHT), cv2.CAP_GSTREAMER)

    print("Press 'q' to quit")

    while True:
        retL, frameL = cap_left.read()
        retR, frameR = cap_right.read()

        if not retL or not retR:
            break

        # 1. Rectify images
        rectified_L = cv2.remap(frameL, map1_L, map2_L, cv2.INTER_LINEAR)
        rectified_R = cv2.remap(frameR, map1_R, map2_R, cv2.INTER_LINEAR)

        # 2. Compute Disparity
        # SGBM works on grayscale
        grayL = cv2.cvtColor(rectified_L, cv2.COLOR_BGR2GRAY)
        grayR = cv2.cvtColor(rectified_R, cv2.COLOR_BGR2GRAY)

        disparity = stereo.compute(grayL, grayR).astype(np.float32) / 16.0

        # 3. Normalize for visualization (Scale to 0-255)
        disp_visual = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        disp_color = cv2.applyColorMap(disp_visual, cv2.COLORMAP_JET)

        # Show results
        cv2.imshow("Left Rectified", rectified_L)
        cv2.imshow("Depth (Disparity)", disp_color)

        key =cv2.waitKey(1)
        # Hit "q" or "ESC" to close the window
        if key == ord('q') or key == 27:
            break
        if key == ord('s'):
            cv2.imwrite("left.jpeg", rectified_L)
            cv2.imwrite("right.jpeg", rectified_R)

    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_depth_sensing()