from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    # Node to translate Twist messages to STM32 serial commands
    serial_bridge_node = Node(
        package='orion_base',
        executable='stm32_bridge_node',
        name='stm32_bridge_node',
        output='screen'
    )

    # Node for keyboard input (publishes to /cmd_vel)
    teleop_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop',
        output='screen',
        prefix='xterm -e'  # Opens a new terminal window to capture your keystrokes
    )

    return LaunchDescription([
        serial_bridge_node,
        teleop_node
    ])