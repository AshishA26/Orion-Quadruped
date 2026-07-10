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

    return LaunchDescription([
    ])