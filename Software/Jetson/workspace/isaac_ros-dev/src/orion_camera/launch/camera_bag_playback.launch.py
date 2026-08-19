import os
from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    orion_camera_dir = get_package_share_directory('orion_camera')
    params_file = os.path.join(orion_camera_dir, 'config', 'params.yaml')

    depth_map_node = Node(
        package='orion_camera',
        executable='depth_map_node',
        name='depth_map_node',
        output='screen',
        parameters=[params_file, {'use_sim_time': True}],
        ros_arguments=['--log-level', 'error'],
        remappings=[
            ('image_raw', 'left/image_raw'),
            ('depth_image_raw', '/depth_image_raw'),
            ('depth_image_color_raw', '/depth_image_color_raw'),
            ('depth_image_color_compressed', '/depth_image_color_compressed'),
        ]
    )
    
    bag_play = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'play',
            '/workspaces/isaac_ros-dev/bags/orion_run_20260818_003319_battery_boxes_depth',
            '--clock',
            '--loop',
        ],
        output='screen',
    )
    
    foxglove_bridge_node = Node(
        package='foxglove_bridge',
        executable='foxglove_bridge',
        name='foxglove_bridge',
        parameters=[{'port': 8765, 'address': '0.0.0.0', 'use_sim_time': True}],
    )

    return LaunchDescription([
        bag_play,
        depth_map_node,
        foxglove_bridge_node
    ])