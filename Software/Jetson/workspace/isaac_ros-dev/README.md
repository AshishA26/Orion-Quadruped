# Isaac ROS Workspace

## Jetson Setup:
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

## Building and running
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

### Bag

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
  /annotated_image_compressed
```