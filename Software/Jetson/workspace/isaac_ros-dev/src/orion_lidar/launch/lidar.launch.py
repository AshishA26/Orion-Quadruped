import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    orion_lidar_dir = get_package_share_directory('orion_lidar')
    params_file = os.path.join(orion_lidar_dir, 'config', 'params.yaml')

    # RPLidar Node (A1M8 Driver)
    rplidar_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        output='screen',
        parameters=[params_file]
    )

    # Calculates odom -> base_link based on laser scan movement
    rf2o_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        parameters=[params_file],
        ros_arguments=['--log-level', 'error']
    )

    # Maps the environment
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[params_file],
        ros_arguments=['--log-level', 'error']
    )

    return LaunchDescription([
        rplidar_node,
        rf2o_node,
        slam_toolbox_node
    ])