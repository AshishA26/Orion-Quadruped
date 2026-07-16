#!/bin/bash

# Dynamically find and set the active Jetson display
function init_docker_display() {
    for d in 0 1; do
        # Suppress output and check if the X server on this display is accepting connections
        if xdpyinfo -display :$d >/dev/null 2>&1; then
            export DISPLAY=:$d
            echo "Successfully set DISPLAY=$DISPLAY"
            return 0
        fi
    done
    return 1
}
init_docker_display

source install/setup.bash
ros2 launch orion_bringup bringup.launch.py
