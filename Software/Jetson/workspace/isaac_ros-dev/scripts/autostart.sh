#! /bin/bash
# Dynamically find and set the active Jetson display
function init_docker_display() {
    for d in 0 1; do
        # Suppress output and check if the X server on this display is accepting connections
        if xdpyinfo -display :$d >/dev/null 2>&1; then
            export DISPLAY=:$d
            echo "Successfully set DISPLAY=$DISPLAY"

            # Grant local X server access for your Docker container
            xhost +local: >/dev/null
            echo "xhost configured for local connections."
            return 0
        fi
    done

    echo "Error: Could not detect an active X server on :0 or :1."
    return 1
}
init_docker_display
export ISAAC_ROS_WS=/home/orion/Documents/Quadruped/Software/Jetson/workspace/isaac_ros-dev
cd ${ISAAC_ROS_WS}/src/submodules/isaac_ros_common && ./scripts/run_autostart.sh --skip_image_build
