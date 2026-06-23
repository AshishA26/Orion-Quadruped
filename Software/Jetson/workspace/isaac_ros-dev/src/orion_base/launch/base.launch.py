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

    # Node to convert raw Joy to Twist
    # Reads from /joy, publishes to /cmd_vel
    # teleop_joy_node = Node(
    #     package='teleop_twist_joy',
    #     executable='teleop_node',
    #     name='teleop_twist_joy_node',
    #     parameters=[{
    #         # Axis mapping PS5 controller
    #         'axis_linear.x': 1,    # Left stick UP/DOWN
    #         'axis_linear.y': 0,    # Left stick LEFT/RIGHT
    #         'axis_angular.yaw': 2, # Right stick LEFT/RIGHT
            
    #         # Max speeds
    #         'scale_linear.x': 1.0,  # Max 1.0 m/s forward
    #         'scale_linear.y': 1.0,  # Max 1.0 m/s strafe
    #         'scale_angular.yaw': 1.0, # Max 1.0 rad/s turn
            
    #         # Require holding the L1 button as a "Deadman Switch" for safety
    #         'enable_button': 4,
    #         'require_enable_button': True
    #     }],
    #     condition=IfCondition(use_joystick)
    # )

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