import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Get the package directories
    orion_base_dir = get_package_share_directory('orion_base')
    orion_lidar_dir = get_package_share_directory('orion_lidar')

    # Include Lidar launch
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(orion_lidar_dir, 'launch', 'lidar.launch.py')
        )
    )

    # Include Base launch
    base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(orion_base_dir, 'launch', 'base.launch.py')
        )
    )

    return LaunchDescription([
        # lidar_launch,
        base_launch
    ])