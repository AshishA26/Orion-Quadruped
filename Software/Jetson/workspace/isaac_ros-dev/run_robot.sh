#!/bin/bash

export DISPLAY=:0
colcon build --symlink-install
source install/setup.bash
ros2 launch orion_bringup bringup.launch.py