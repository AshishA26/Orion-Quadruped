import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    
    # --- 1. RPLidar Node (A1M8 Driver) ---
    rplidar_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        output='screen',
        parameters=[{
            'serial_port': '/dev/ttyUSB0',
            'serial_baudrate': 115200,  # A1M8 specific 
            'frame_id': 'laser',
            'inverted': False,
            'angle_compensate': True,
        }]
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
        parameters=[{
            'laser_scan_topic': '/scan',
            'odom_topic': '/odom',
            'publish_tf': True,
            'base_frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'init_pose_from_topic': '',
            'freq': 10.0
        }]
    )

    # --- 4. SLAM Toolbox ---
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'odom_frame': 'odom',
            'map_frame': 'map',
            'base_frame': 'base_link',
            'scan_topic': '/scan',
            'mode': 'mapping', # defaults to mapping
            # RF2O specific tuning for SLAM
            'minimum_travel_distance': 0.1,
            'transform_timeout': 0.5,
        }]
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