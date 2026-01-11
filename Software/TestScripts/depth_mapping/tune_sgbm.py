'''
Tune disparity map created with StereoSGBM algorithim

Press 'l' to load parameters from json file
Press 's' to save parameters to json file

Note: Negative parameters are not able to be properly loaded, and need to be set manually
'''
print(__doc__)

import cv2
import numpy as np
import json

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

def nothing(x):
    pass

cv2.namedWindow('DepthMap',cv2.WINDOW_NORMAL)
cv2.namedWindow('disp',cv2.WINDOW_NORMAL)
cv2.resizeWindow('disp',600,600)

cv2.createTrackbar('minDisparity','disp',0,500,nothing) # arbitary upper limit
cv2.setTrackbarMin('minDisparity', 'disp', -500) # arbitary lower limit
cv2.createTrackbar('numDisparities','disp',1,500,nothing) # arbitary upper limit
cv2.setTrackbarMin('numDisparities', 'disp', 1) 
cv2.createTrackbar('blockSize','disp',15,255,nothing)
cv2.setTrackbarMin('blockSize', 'disp', 1) # pixelwise
cv2.createTrackbar('preFilterCap','disp',5,63,nothing)
cv2.setTrackbarMin('preFilterCap','disp',1)
cv2.createTrackbar('uniquenessRatio','disp',15,100,nothing)
cv2.setTrackbarMin('uniquenessRatio','disp',1)
cv2.createTrackbar('speckleRange','disp',1,200,nothing)
cv2.setTrackbarMin('speckleRange', 'disp', 1)
cv2.createTrackbar('speckleWindowSize','disp',1,300,nothing)
cv2.createTrackbar('disp12MaxDiff','disp',0,500,nothing)
cv2.createTrackbar('p1','disp',2,4000,nothing) # arbitrary
cv2.createTrackbar('p2','disp',5,20000,nothing) # arbitrary
cv2.createTrackbar('mode','disp',0,2,nothing) # SGBM, HH, SGBM_3WAY

def save_map_settings():
    settings = {}
    # Updating the parameters based on the trackbar positions
    settings['minDisparity'] = cv2.getTrackbarPos('minDisparity','disp')
    settings['numDisparities'] = cv2.getTrackbarPos('numDisparities','disp')
    settings['blockSize'] = cv2.getTrackbarPos('blockSize','disp')
    settings['preFilterCap'] = cv2.getTrackbarPos('preFilterCap','disp')
    settings['uniquenessRatio'] = cv2.getTrackbarPos('uniquenessRatio','disp')
    settings['speckleRange'] = cv2.getTrackbarPos('speckleRange','disp')
    settings['speckleWindowSize'] = cv2.getTrackbarPos('speckleWindowSize','disp')
    settings['disp12MaxDiff'] = cv2.getTrackbarPos('disp12MaxDiff','disp')
    settings['mode'] = cv2.getTrackbarPos('mode','disp')
    settings['p1'] = cv2.getTrackbarPos('p1','disp')
    settings['p2'] = cv2.getTrackbarPos('p2','disp')
    with open('settings.json', 'w') as file:
        json_string = json.dumps(settings, sort_keys=True, indent=4)
        file.write(json_string)
    print ('Settings saved to file')

def load_map_settings():
    settings={}
    with open('settings.json') as f:
        settings = json.load(f)
    # Unable to set negative value in Trackbar... OpenCV Bug
    cv2.setTrackbarPos('minDisparity','disp',settings['minDisparity'])
    cv2.setTrackbarPos('numDisparities','disp',settings['numDisparities'])
    cv2.setTrackbarPos('blockSize','disp',settings['blockSize'])
    cv2.setTrackbarPos('preFilterCap','disp',settings['preFilterCap'])
    cv2.setTrackbarPos('uniquenessRatio','disp',settings['uniquenessRatio'])
    cv2.setTrackbarPos('speckleRange','disp',settings['speckleRange'])
    cv2.setTrackbarPos('speckleWindowSize','disp',settings['speckleWindowSize'])
    cv2.setTrackbarPos('disp12MaxDiff','disp',settings['disp12MaxDiff'])
    cv2.setTrackbarPos('mode','disp',settings['mode'])
    cv2.setTrackbarPos('p1','disp',settings['p1'])
    cv2.setTrackbarPos('p2','disp',settings['p2'])
    print ('Settings loaded from file')

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
        
        # Updating the parameters based on the trackbar positions
        minDisparity = cv2.getTrackbarPos('minDisparity','disp')
        numDisparities = cv2.getTrackbarPos('numDisparities','disp')
        blockSize = cv2.getTrackbarPos('blockSize','disp')
        preFilterCap = cv2.getTrackbarPos('preFilterCap','disp')
        uniquenessRatio = cv2.getTrackbarPos('uniquenessRatio','disp')
        speckleRange = cv2.getTrackbarPos('speckleRange','disp')
        speckleWindowSize = cv2.getTrackbarPos('speckleWindowSize','disp')
        disp12MaxDiff = cv2.getTrackbarPos('disp12MaxDiff','disp')
        p1 = cv2.getTrackbarPos('p1','disp')
        p2 = cv2.getTrackbarPos('p2','disp')
        mode = cv2.getTrackbarPos('mode','disp')

        # Setting the updated parameters before computing disparity map
        stereo.setMinDisparity(minDisparity)
        stereo.setNumDisparities(numDisparities)
        stereo.setBlockSize(blockSize)
        stereo.setPreFilterCap(preFilterCap)
        stereo.setUniquenessRatio(uniquenessRatio)
        stereo.setSpeckleRange(speckleRange)
        stereo.setSpeckleWindowSize(speckleWindowSize)
        stereo.setDisp12MaxDiff(disp12MaxDiff)
        stereo.setP1(p1)
        stereo.setP2(p2)
        stereo.setMode(mode)

        disparity = stereo.compute(grayL, grayR).astype(np.float32)
        # Scaling down the disparity values and normalizing them 
        disparity = (disparity/16.0 - minDisparity)/numDisparities

        # 3. Normalize for visualization (Scale to 0-255)
        disp_normal = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        disp_color = cv2.applyColorMap(disp_normal, cv2.COLORMAP_JET)

        # Show results
        cv2.imshow("DepthMap", np.hstack((disp_color, frameL)))

        key =cv2.waitKey(1)
        # Hit "q" or "ESC" to close the window
        if key == ord('q') or key == 27:
            break
        if key == ord('s'):
            save_map_settings()
        if key == ord('l'):
            load_map_settings()

    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_depth_sensing()