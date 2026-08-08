from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    orion_base_dir = get_package_share_directory('orion_base')
    params_file = os.path.join(orion_base_dir, 'config', 'params.yaml')

    # Joystick Node - Node to read the raw PS5 Bluetooth device
    # Publishes to /joy
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[params_file],
    )

    joystick_parser_node = Node(
        package="orion_base",
        executable="joystick_parser_node",
        name="joystick_parser_node",
        output="screen",
        parameters=[params_file],
        remappings=[
            ('joy', '/joy'),
            ('joy_motion_cmd', '/joy_motion_cmd'),
            ('joy_eyes_cmd', '/joy_eyes_cmd'),
        ]
    )

    stm32_bridge_node = Node(
        package='orion_base',
        executable='stm32_bridge_node',
        name='stm32_bridge_node',
        output='screen',
        parameters=[params_file],
        remappings=[
            ('orion_motion_cmd', '/orion_motion_cmd'),
            ('battery_voltage_front', '/battery_voltage_front'),
            ('battery_voltage_rear', '/battery_voltage_rear'),
            ('battery_voltage_jetson', '/battery_voltage_jetson'),
            ('imu_degrees', '/imu_degrees')
        ]
    )

    roboeyes_node = Node(
        package='orion_base',
        executable='roboeyes_node',
        name='roboeyes_node',
        output='screen',
        parameters=[params_file],
        remappings=[
            ('orion_eyes_cmd', '/orion_eyes_cmd'),
        ]
    )

    cmd_mux_node = Node(
        package='orion_base',
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

    foxglove_bridge_node = Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            parameters=[{'port': 8765, 'address': '0.0.0.0'}],
        )

    return LaunchDescription([
        stm32_bridge_node,
        joy_node,
        joystick_parser_node,
        roboeyes_node,
        cmd_mux_node,
        foxglove_bridge_node
    ])