
Run the following on the jetson:
```bash
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyTHS1
sudo chmod 666 /dev/input/js0
cd ${ISAAC_ROS_WS}/src/isaac_ros_common && ./scripts/run_dev.sh
./install_deps.sh
colcon build --symlink-install
source install/setup.bash
ros2 launch orion_lidar lidar.launch.py
ros2 launch orion_base base.launch.py
```


Dockerfile.Orion contains (goes into src/isaac_ros_common/docker/Dockerfile.orion):

```
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

RUN apt-get update && apt-get install -y \
    ros-humble-slam-toolbox \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-sllidar-ros2 \
    ros-humble-xacro \
    ros-humble-teleop-twist-keyboard \
    ros-humble-joy \
    ros-humble-teleop-twist-joy \
    python3-serial \
    xterm

ENV LD_LIBRARY_PATH=/opt/ros/humble/share/gxf_isaac_optimizer/gxf/lib:${LD_LIBRARY_PATH}
RUN echo "source /opt/ros/humble/setup.bash" >> /etc/bash.bashrc
```