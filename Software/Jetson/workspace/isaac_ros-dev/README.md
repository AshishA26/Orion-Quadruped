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