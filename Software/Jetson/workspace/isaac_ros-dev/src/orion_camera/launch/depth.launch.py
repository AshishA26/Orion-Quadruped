import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    orion_camera_dir = get_package_share_directory('orion_camera')
    params_file = os.path.join(orion_camera_dir, 'config', 'params.yaml')

    depth_map_node = Node(
        package='orion_camera',
        executable='depth_map_node',
        name='depth_map_node',
        output='screen',
        parameters=[params_file],
        remappings=[
            ('image_raw', 'left/image_raw'),
            ('depth_image_raw', '/depth_image_raw'),
            ('depth_image_color_raw', '/depth_image_color_raw'),
            ('depth_image_color_compressed', '/depth_image_color_compressed'),
        ]
    )

    return LaunchDescription([depth_map_node])
