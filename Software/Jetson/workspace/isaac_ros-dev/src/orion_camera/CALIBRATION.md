# IMX219-83 Stereo Camera Calibration Guide

This guide walks through calibrating both cameras on the IMX219-83 dual CSI module using a checkerboard pattern. Since the IMX219-83 has **no EEPROM**, calibration data must be generated manually and saved to YAML files.

## Prerequisites

- A printed checkerboard pattern (recommended: 9×6 inner corners, 25mm squares)
  - Print on rigid cardboard — do not use a screen
  - Measure the actual square size after printing (printers often scale)
- ROS 2 camera calibration package:
  ```bash
  sudo apt-get install ros-humble-camera-calibration
  ```

## Step 1: Start the Camera Node

Use either the GStreamer or Isaac ROS Argus solution to publish camera images:

```bash
# Option A: GStreamer (simpler, no Isaac container needed)
ros2 launch orion_camera gstreamer_camera.launch.py

# Option B: Isaac ROS Argus (inside Isaac ROS container)
ros2 launch orion_camera camera.launch.py
```

Verify images are publishing:
```bash
ros2 topic list | grep image_raw
# Should show:
#   /left/image_raw
#   /right/image_raw
```

## Step 2: Calibrate the Left Camera

Run the calibration tool pointing at the left camera topics:

```bash
ros2 run camera_calibration cameracalibrator \
  --size 8x5 \
  --square 0.025 \
  --no-service-check \
  image:=/left/image_raw \
  camera:=/left
```

> **Note**: `--size` is inner corners (columns-1 x rows-1). For a 9×6 checkerboard, use `8x5`.

- Move the checkerboard slowly through the camera's field of view
- Cover all edges and corners of the image
- Tilt the board at various angles
- The calibration bars (X, Y, Size, Skew) should all turn green
- Click **CALIBRATE** when all bars are green
- Click **SAVE** to export the calibration data
- Click **COMMIT** if available

The calibration file is saved to `/tmp/calibrationdata.tar.gz`. Extract it:

```bash
cd /tmp && tar xzf calibrationdata.tar.gz
# The YAML file is at: /tmp/ost.yaml
```

Copy it to the camera config:
```bash
cp /tmp/ost.yaml $(ros2 pkg prefix orion_camera)/share/orion_camera/config/left_camera_info.yaml
# Or copy to the source tree:
cp /tmp/ost.yaml src/orion_camera/config/left_camera_info.yaml
```

## Step 3: Calibrate the Right Camera

Repeat the same process for the right camera:

```bash
ros2 run camera_calibration cameracalibrator \
  --size 8x5 \
  --square 0.025 \
  --no-service-check \
  image:=/right/image_raw \
  camera:=/right
```

Save and copy to `right_camera_info.yaml`.

## Step 4: Verify Calibration

After copying both calibration files, restart the camera node and check that `CameraInfo` messages contain the correct values:

```bash
ros2 topic echo /left/camera_info --once
ros2 topic echo /right/camera_info --once
```

You can also visually verify with `rqt_image_view`:
```bash
ros2 run rqt_image_view rqt_image_view
```

## Calibration File Format

Both files use the standard ROS camera calibration YAML format:

```yaml
image_width: 1920
image_height: 1080
camera_name: left_camera
camera_matrix:
  rows: 3
  cols: 3
  data: [fx, 0, cx, 0, fy, cy, 0, 0, 1]
distortion_model: plumb_bob
distortion_coefficients:
  rows: 1
  cols: 5
  data: [k1, k2, p1, p2, k3]
rectification_matrix:
  rows: 3
  cols: 3
  data: [1, 0, 0, 0, 1, 0, 0, 0, 1]
projection_matrix:
  rows: 3
  cols: 4
  data: [fx', 0, cx', 0, 0, fy', cy', 0, 0, 0, 1, 0]
```

## Notes

- The approximate IMX219 intrinsics in the placeholder files (fx=fy≈1380 at 1080p) are reasonable starting points but will be off by 5-15% per sensor.
- Each sensor MUST be calibrated individually — manufacturing tolerances mean the two sensors on the IMX219-83 will have slightly different intrinsics.
- If you change the capture resolution, you must re-calibrate.
- For stereo extrinsics (baseline, relative rotation), use `ros2 run camera_calibration cameracalibrator --stereo` with both camera topics simultaneously.
