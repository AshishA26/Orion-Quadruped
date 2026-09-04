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

    use_custom_pure_pursuit = LaunchConfiguration('use_custom_pure_pursuit')
    declare_use_custom_pp_cmd = DeclareLaunchArgument(
        'use_custom_pure_pursuit',
        default_value='true',
        description='Whether to use the custom pure pursuit node or Nav2 Regulated Pure Pursuit'
    )

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

    # Custom Pure Pursuit Node
    pure_pursuit_node = Node(
        package='orion_navigation',
        executable='pure_pursuit_node',
        name='pure_pursuit_node',
        parameters=[params_file],
        output='screen',
        condition=IfCondition(use_custom_pure_pursuit),
        remappings=[
            ('plan', '/plan'),                        # Nav2 planned path (from planner_server)
            ('nav_motion_cmd', '/nav_motion_cmd'),    # Consumed by cmd_mux_node
        ],
    )
    
    # Velocity Smoother / cmd_vel remapper for Nav2 Pure Pursuit
    # Nav2 outputs to cmd_vel. We want it to publish to nav_motion_cmd
    remap_cmd_vel_node = Node(
        package='topic_tools',
        executable='relay',
        name='cmd_vel_relay',
        arguments=['cmd_vel', 'nav_motion_cmd'],
        condition=UnlessCondition(use_custom_pure_pursuit)
    )

    return LaunchDescription([
        declare_use_custom_pp_cmd,
        navigation_launch,
        pure_pursuit_node,
        remap_cmd_vel_node
    ])