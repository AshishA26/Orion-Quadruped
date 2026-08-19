import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Get the package directories
    orion_base_dir = get_package_share_directory('orion_base')
    orion_lidar_dir = get_package_share_directory('orion_lidar')
    orion_nav_dir = get_package_share_directory('orion_navigation')
    orion_camera_dir = get_package_share_directory('orion_camera')
    orion_urdf_dir = get_package_share_directory('orion_urdf')

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

    # Include Navigation launch
    nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(orion_nav_dir, 'launch', 'navigation.launch.py')
        )
    )

    # Include Camera launch (Isaac ROS Argus — GPU-accelerated, zero-copy)
    # camera_launch = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(
    #         os.path.join(orion_camera_dir, 'launch', 'argus_dual_camera.launch.py')
    #     )
    # )
    # Alternative: GStreamer camera (no Isaac container dependency)
    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(orion_camera_dir, 'launch', 'gstreamer_dual_camera.launch.py')
        )
    )

    hand_pose_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(orion_camera_dir, 'launch', 'hand_pose.launch.py')
        )
    )

    depth_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(orion_camera_dir, 'launch', 'depth.launch.py')
        )
    )

    urdf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(orion_urdf_dir, 'launch', 'view_robot.launch.py')
        )
    )

    return LaunchDescription([
        lidar_launch,
        base_launch,
        nav_launch,
        camera_launch,
        hand_pose_launch,
        urdf_launch,
        # depth_launch
    ])