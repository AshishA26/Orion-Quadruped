#! /bin/bash
export ISAAC_ROS_WS=/home/orion/Documents/Quadruped/Software/Jetson/workspace/isaac_ros-dev
cd ${ISAAC_ROS_WS}/src/submodules/isaac_ros_common && ./scripts/run_autostart.sh --skip_image_build
