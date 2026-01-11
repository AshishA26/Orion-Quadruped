

```bash
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0
cd ${ISAAC_ROS_WS}/src/isaac_ros_common && ./scripts/run_dev.sh
./install_deps.sh
colcon build --symlink-install
source install/setup.bash
ros2 launch orion_lidar lidar.launch.py
```