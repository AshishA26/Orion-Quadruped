import os
from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg = get_package_share_directory('orion_urdf')
    urdf_file = PathJoinSubstitution([pkg, 'urdf', 'robot_description.urdf']) 
    robot_description = Command(['xacro ', urdf_file])
    orion_lidar_dir = get_package_share_directory('orion_lidar')
    params_file = os.path.join(orion_lidar_dir, 'config', 'params.yaml')

    # Publishes TF from the URDF
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True},],
        output='screen'
    )
    joint_state_republisher = Node(
        package='orion_base',
        executable='joint_state_republisher',
        name='joint_state_republisher',
        output='screen',
        parameters=[
            {'use_sim_time': True},
        ],
    )
    rf2o_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        parameters=[params_file, {'use_sim_time': True}],
        ros_arguments=['--log-level', 'error']
    )
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[params_file, {'use_sim_time': True}],
        ros_arguments=['--log-level', 'error']
    )
    bag_play = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'play',
            '/workspaces/isaac_ros-dev/bags/orion_run_20260818_004807_slam',
            '--clock',
            '--remap', '/odom:=/recorded_odom',
            '--remap', '/map:=/recorded_map',
            '--remap', '/map_metadata:=/recorded_map_metadata',
            '--remap', '/parameter_events:=/recorded_parameter_events',
            '--remap', '/pose:=/recorded_pose',
            '--remap', '/rosout:=/recorded_rosout',
            '--remap', '/slam_toolbox/graph_visualization:=/recorded_slam_toolbox/graph_visualization',
            '--remap', '/slam_toolbox/scan_visualization:=/recorded_slam_toolbox/scan_visualization',
            '--remap', '/slam_toolbox/update:=/recorded_slam_toolbox/update',
        ],
        output='screen',
    )
    
    foxglove_bridge_node = Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            parameters=[{'port': 8765, 'address': '0.0.0.0', 'use_sim_time': True}],
        )

    return LaunchDescription([
        robot_state_publisher,
        slam_toolbox_node,
        bag_play,
        rf2o_node,
        joint_state_republisher,
        foxglove_bridge_node
    ])