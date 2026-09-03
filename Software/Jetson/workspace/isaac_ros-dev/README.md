# Isaac ROS Workspace

ROS2 workspace running on the NVIDIA Jetson Orin Nano inside an Isaac ROS Docker container.

## ROS2 Packages

### `orion_base`
Core system nodes.

| Node | Description |
|:-----|:------------|
| `stm32_bridge_node` | Bidirectional UART bridge to STM32 — sends motion commands, receives IMU/battery/joint telemetry |
| `joystick_parser_node` | Parses joystick input into motion and eye commands |
| `cmd_mux_node` | Multiplexes joystick and autonomous navigation commands |
| `roboeyes_node` | OLED eye animations via Python/OpenCV, controlled over ROS2 topics |
| `joint_state_republisher` | Republishes STM32 joint angles as standard `JointState` messages |

### `orion_camera`
| Node | Description |
|:-----|:------------|
| `gstreamer_dual_camera_node` | Dual CSI (IMX219) capture via GStreamer |
| `depth_map_node` | MIDAS depth inference with TensorRT |
| `hand_pose_node` | MediaPipe hand gesture recognition |

### `orion_lidar`
- RPLIDAR A1M8 driver — publishes `/scan` for SLAM and navigation.
- `slam_toolbox` for 2D SLAM.
- `rf2o` for laser odometry

### `orion_navigation`
- `nav2` for costmap creation and pure-pursuit path following.

### `orion_bringup`
- Main `bringup.launch.py`.

### `orion_msgs`
- Custom messages: `OrionMotionCmd`, `OrionEyesCmd`, `OrionBatteryVoltage`, `OrionImuFeedback`, `OrionLegInfo`.

### `orion_urdf`
- Full URDF with SolidWorks-exported STL meshes.

### `submodules/`
- `isaac_ros_common`
- `isaac_ros_argus_camera`
- `rf2o_laser_odometry`

## Directory Structure

```
isaac_ros-dev/
├── src/                  # ROS2 packages (see above)
├── scripts/
│   ├── build_robot.sh    # Colcon build
│   ├── run_robot.sh      # Launch with auto display detection
│   ├── autostart.sh      # Systemd entry point
│   └── foxglove-layouts/ # Foxglove dashboard layouts
└── models/
    ├── midas_v21_small_256.onnx   # MIDAS ONNX model
    └── midas_v21_small_256.plan   # TensorRT compiled plan
```

---

## Jetson Setup
```bash
cd ${ISAAC_ROS_WS}
cp src/orion_bringup/docker/.isaac_ros_common-config ~/.
# Systemd services
sudo cp src/orion_bringup/services/* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable orion-startup.service
sudo systemctl start orion-startup.service
```

### Checking
```bash
sudo systemctl status orion-startup.service
journalctl -b -u orion-startup.service 
journalctl -af -u orion-startup.service 
```

## Building and Running
```bash
cp src/orion_bringup/docker/.isaac_ros_common-config ~/.
cd ${ISAAC_ROS_WS}/src/submodules/isaac_ros_common && ./scripts/run_dev.sh --skip_image_build
./scripts/build_robot.sh
./scripts/run_robot.sh
```

## Notes
### ROS
Creating a package (when inside docker container):
```bash
cd src
ros2 pkg create --build-type ament_python orion_bringup
```

### General
To fix SSH / connectivity issues from no machine or vs-code, ensure you have the right wifi set, and are on MAXN Super power mode.

### Bag Recording

All (no depth):
```bash
ros2 bag record \
  --storage mcap \
  -o orion_run_$(date +%Y%m%d_%H%M%S) \
  /battery_voltage_front \
  /battery_voltage_jetson \
  /battery_voltage_rear \
  /imu_degrees \
  /joint_angles_back_left \
  /joint_angles_back_right \
  /joint_angles_front_left \
  /joint_angles_front_right \
  /left/camera_info \
  /left/image_compressed \
  /left/image_raw \
  /odom \
  /map \
  /scan \
  /global_costmap/costmap \
  /local_costmap/costmap \
  /plan \
  /robot_description \
  /orion_eyes_cmd \
  /orion_motion_cmd \
  /map_metadata \
  /landmarks \
  /slam_toolbox/update \
  /slam_toolbox/scan_visualization \
  /slam_toolbox/graph_visualization \
  /slam_toolbox/feedback \
  /rosout \
  /pose \
  /joy_motion_cmd \
  /joy_eyes_cmd \
  /joy \
  /annotated_image_compressed \
  /foxglove_bridge/sysinfo \
  /tf \
  /tf_static
```

Just cameras (no depth):
```bash
ros2 bag record \
  --storage mcap \
  -o orion_run_$(date +%Y%m%d_%H%M%S) \
  /left/camera_info \
  /left/image_compressed \
  /left/image_raw \
  /annotated_image_compressed
```

Everything but cameras:
```bash
ros2 bag record \
  --storage mcap \
  -o orion_run_$(date +%Y%m%d_%H%M%S) \
  /battery_voltage_front \
  /battery_voltage_jetson \
  /battery_voltage_rear \
  /imu_degrees \
  /joint_angles_back_left \
  /joint_angles_back_right \
  /joint_angles_front_left \
  /joint_angles_front_right \
  /odom \
  /map \
  /scan \
  /global_costmap/costmap \
  /local_costmap/costmap \
  /plan \
  /robot_description \
  /orion_eyes_cmd \
  /orion_motion_cmd \
  /map_metadata \
  /landmarks \
  /slam_toolbox/update \
  /slam_toolbox/scan_visualization \
  /slam_toolbox/graph_visualization \
  /slam_toolbox/feedback \
  /rosout \
  /pose \
  /joy_motion_cmd \
  /joy_eyes_cmd \
  /joy \
  /foxglove_bridge/sysinfo \
  /tf \
  /tf_static
```