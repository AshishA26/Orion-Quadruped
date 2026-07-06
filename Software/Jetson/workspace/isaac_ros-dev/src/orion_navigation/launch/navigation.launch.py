from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    orion_navigation_dir = get_package_share_directory('orion_navigation')
    params_file = os.path.join(orion_navigation_dir, 'config', 'params.yaml')

    cmd_mux_node = Node(
        package='orion_navigation',
        executable='cmd_mux_node',
        name='cmd_mux_node',
        output='screen',
        parameters=[params_file],
        remappings=[
            ('joy_motion_cmd', '/joy_motion_cmd'),
            ('joy_eyes_cmd', '/joy_eyes_cmd'),
            ('nav_motion_cmd', '/nav_motion_cmd'),
            ('orion_motion_cmd', '/orion_motion_cmd'),
            ('orion_eyes_cmd', '/orion_eyes_cmd'),
        ]
    )

    return LaunchDescription([
        cmd_mux_node,
    ])