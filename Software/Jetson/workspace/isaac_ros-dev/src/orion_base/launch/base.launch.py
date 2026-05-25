from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node

def generate_launch_description():
    
    # Launch Argument
    use_joystick_arg = DeclareLaunchArgument(
        'use_joystick',
        default_value='false',
        description='Set to "true" to use PS5 controller, "false" for keyboard'
    )
    use_joystick = LaunchConfiguration('use_joystick')

    # Node to translate Twist messages to STM32 serial commands
    serial_bridge_node = Node(
        package='orion_base',
        executable='stm32_bridge_node',
        name='stm32_bridge_node',
        output='screen'
    )

    # Node for keyboard input (publishes to /cmd_vel)
    teleop_keyboard_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_keyboard',
        output='screen',
        prefix='xterm -e',   # Opens a new terminal window to capture your keystrokes
        condition=UnlessCondition(use_joystick)  # Basically is "if not true"
    )

    # Joystick Node - Node to read the raw PS5 Bluetooth device
    # (Launch only if use_joystick is true)
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'device_id': 0,        # Refers to /dev/input/js0
            'deadzone': 0.05,      # Ignore tiny stick drifts
            'autorepeat_rate': 20.0 # Force sending 20 messages a second even if holding still
        }],
        condition=IfCondition(use_joystick)
    )

    # Node to convert raw Joy to Twist
    teleop_joy_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        parameters=[{
            # Axis mapping (Standard for PS5)
            'axis_linear.x': 1,    # Left stick UP/DOWN
            'axis_linear.y': 0,    # Left stick LEFT/RIGHT
            'axis_angular.yaw': 3, # Right stick LEFT/RIGHT
            
            # Max speeds (Tune these based on how fast your dog can physically step)
            'scale_linear.x': 0.5,  # Max 0.5 m/s forward
            'scale_linear.y': 0.5,  # Max 0.5 m/s strafe
            'scale_angular.yaw': 1.0, # Max 1.0 rad/s turn
            
            # Require holding the L1 button (Button index 4) as a "Deadman Switch" to move
            'enable_button': 4,
            'require_enable_button': True
        }],
        condition=IfCondition(use_joystick)
    )

    return LaunchDescription([
        use_joystick_arg,
        serial_bridge_node,
        teleop_keyboard_node,
        joy_node,
        teleop_joy_node
    ])