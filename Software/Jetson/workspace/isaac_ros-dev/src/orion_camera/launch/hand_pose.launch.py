import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    orion_camera_dir = get_package_share_directory('orion_camera')
    params_file = os.path.join(orion_camera_dir, 'config', 'params.yaml')

    hand_pose_node = Node(
        package='orion_camera',
        executable='hand_pose_node',
        name='hand_pose_node',
        output='screen',
        parameters=[params_file],
        remappings=[
            ('image_raw', 'left/image_raw'),
            ('annotated_image_raw', 'annotated_image_raw'),
            ('annotated_image_compressed', 'annotated_image_compressed'),
            ('landmarks', 'landmarks'),
        ]
    )

    return LaunchDescription([hand_pose_node])
