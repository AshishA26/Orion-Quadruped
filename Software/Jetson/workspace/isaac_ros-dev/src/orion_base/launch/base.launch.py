from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node

def generate_launch_description():
    # Current setup for joystick commands to stm32:
    #   Joystick -> joy_node -> stm32_bridge_node

    # Joystick Node - Node to read the raw PS5 Bluetooth device
    # Publishes to /joy
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'device_id': 0,         # /dev/input/js0
            'deadzone': 0.05,       # Ignore small stick drifts
            'autorepeat_rate': 50.0 # Force sending 50 messages a second even if holding still (matches stm32 Hz)
        }],
    )

    # Node to translate Twist messages to STM32 serial commands
    # Reads from /joy
    stm32_bridge_node = Node(
        package='orion_base',
        executable='stm32_bridge_node',
        name='stm32_bridge_node',
        output='screen'
    )

    return LaunchDescription([
        stm32_bridge_node,
        joy_node,
    ])