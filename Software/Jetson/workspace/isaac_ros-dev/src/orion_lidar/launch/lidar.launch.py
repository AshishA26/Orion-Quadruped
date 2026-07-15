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

    # --- 1. RPLidar Node (A1M8 Driver) ---
    rplidar_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        output='screen',
        parameters=[params_file]
    )

    # --- 2. Static TF (base_link -> laser) ---
    # This connects your robot base to the lidar. 
    # Adjust args: x y z yaw pitch roll
    base_to_laser_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_laser_broadcaster',
        arguments=['0.1', '0', '0.05', '0', '0', '0', 'base_link', 'laser']
    )

    # --- 3. RF2O Laser Odometry ---
    # Calculates odom -> base_link based on laser scan movement
    rf2o_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        parameters=[params_file]
    )

    # --- 4. SLAM Toolbox ---
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[params_file]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', '/workspaces/isaac_ros-dev/src/orion_lidar/rviz_configs/mapping.rviz'],
    )

    return LaunchDescription([
        rplidar_node,
        base_to_laser_tf,
        rf2o_node,
        slam_toolbox_node,
        rviz_node
    ])