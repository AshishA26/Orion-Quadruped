from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg = get_package_share_directory('orion_urdf')
    urdf_file = PathJoinSubstitution([pkg, 'urdf', 'robot_description.urdf']) 
    robot_description = Command(['xacro ', urdf_file])

    # Publishes TF from the URDF
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher,
    ])