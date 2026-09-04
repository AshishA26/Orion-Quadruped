from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    orion_navigation_dir = get_package_share_directory('orion_navigation')
    params_file = os.path.join(orion_navigation_dir, 'config', 'params.yaml')

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'params_file': params_file,
            'use_sim_time': 'false',
            'autostart': 'true',
        }.items()
    )

    pure_pursuit_node = Node(
        package='orion_navigation',
        executable='pure_pursuit_node',
        name='pure_pursuit_node',
        parameters=[params_file],
        output='screen',
        remappings=[
            ('plan', '/plan'),                        # Nav2 planned path (from planner_server)
            ('nav_motion_cmd', '/nav_motion_cmd'),    # Consumed by cmd_mux_node
        ],
    )

    return LaunchDescription([
        navigation_launch,
        pure_pursuit_node,
    ])