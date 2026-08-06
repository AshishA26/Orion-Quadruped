# Isaac ROS Argus Camera launch for IMX219-83 dual CSI camera.
# Launches two ArgusMonoNode instances (one per sensor) since the
# IMX219-83 has two independent sensors with no hardware sync.

import os
from ament_index_python.packages import get_package_share_directory
import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    orion_camera_dir = get_package_share_directory('orion_camera')
    params_file = os.path.join(orion_camera_dir, 'config', 'params.yaml')

    # --- Left Camera (CSI sensor_id=0) ---
    argus_left = ComposableNode(
        name='argus_left',
        package='isaac_ros_argus_camera',
        plugin='nvidia::isaac_ros::argus::ArgusMonoNode',
        namespace='argus',
        remappings=[
            ('left/image_raw', 'image_raw'),
            ('left/camera_info', 'camera_info'),
        ],
        parameters=[params_file],
    )

    # --- Right Camera (CSI sensor_id=1) ---
    argus_right = ComposableNode(
        name='argus_right',
        package='isaac_ros_argus_camera',
        plugin='nvidia::isaac_ros::argus::ArgusMonoNode',
        namespace='argus',
        remappings=[
            ('left/image_raw', 'image_raw'),
            ('left/camera_info', 'camera_info'),
        ],
        parameters=[params_file],
    )

    # --- Container ---
    # Both nodes share a single multi-threaded container for
    # zero-copy GPU-accelerated capture.
    argus_container = ComposableNodeContainer(
        name='argus_dual_camera_container',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=[argus_left, argus_right],
        namespace='',
        output='screen',
        arguments=['--ros-args', '--log-level', 'info'],
    )

    return launch.LaunchDescription([argus_container])
