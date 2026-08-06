import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    orion_camera_dir = get_package_share_directory('orion_camera')
    params_file = os.path.join(orion_camera_dir, 'config', 'params.yaml')

    gstreamer_dual_camera_node = Node(
        package='orion_camera',
        executable='gstreamer_dual_camera_node',
        name='gstreamer_dual_camera_node',
        output='screen',
        parameters=[params_file],
        remappings=[
            ('left/image_raw', 'left/image_raw'),
            ('left/image_compressed', 'left/image_compressed'),
            ('left/camera_info', 'left/camera_info'),
            ('right/image_raw', 'right/image_raw'),
            ('right/image_compressed', 'right/image_compressed'),
            ('right/camera_info', 'right/camera_info'),
        ]
    )

    return LaunchDescription([gstreamer_dual_camera_node])
