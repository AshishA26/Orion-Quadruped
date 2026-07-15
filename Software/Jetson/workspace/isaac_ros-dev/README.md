# Isaac ROS Workspace
New commands to run for simplicity:
```bash
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyTHS1
sudo chmod 666 /dev/input/js0
cd ${ISAAC_ROS_WS}/src/isaac_ros_common && ./scripts/run_dev.sh --skip_image_build
./install_deps.sh
./run_robot.sh # Run only this command when making changes to the code
```

Do this once on the jetson:
```bash
# Grant access to serial comm ports (lidar, stm) and human interface devices (joystick)
sudo usermod -a -G dialout,input $USER 
```

## Notes

Old commands (can ignore):
```bash
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
    xterm \
    ros-humble-foxglove-bridge

ENV LD_LIBRARY_PATH=/opt/ros/humble/share/gxf_isaac_optimizer/gxf/lib:${LD_LIBRARY_PATH}
RUN echo "source /opt/ros/humble/setup.bash" >> /etc/bash.bashrc
```



Creating a package (when inside docker container):
```bash
cd src
ros2 pkg create --build-type ament_python orion_bringup
```



Note: Ensure that run_robot.sh is an executable using `chmod +x run_robot.sh`



Note: .bashrc has
```bash
export ISAAC_ROS_WS=/home/orion/Documents/Quadruped/Software/Jetson/workspace/isaac_ros-dev
export CONFIG_IMAGE_KEY="ros2_humble.orion"
export CONFIG_DOCKER_SEARCH_DIRS=(/home/orion/Documents/Quadruped/Software/Jetson/workspace/isaac_ros-dev)
export DISPLAY=:1
xhost +local:root > /dev/null 2>&1
```