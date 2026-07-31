# SPDX-FileCopyrightText: Orion Quadruped Project
# Copyright (c) 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# GStreamer-based dual CSI camera launch file for IMX219-83.
# Alternative to the Isaac ROS Argus solution — uses nvarguscamerasrc
# via OpenCV GStreamer backend. Works outside the Isaac ROS container.

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    orion_camera_dir = get_package_share_directory('orion_camera')

    default_left_cal = os.path.join(
        orion_camera_dir, 'config', 'left_camera_info.yaml')
    default_right_cal = os.path.join(
        orion_camera_dir, 'config', 'right_camera_info.yaml')

    launch_args = [
        DeclareLaunchArgument(
            'capture_width', default_value='1920',
            description='Capture width in pixels.'
        ),
        DeclareLaunchArgument(
            'capture_height', default_value='1080',
            description='Capture height in pixels.'
        ),
        DeclareLaunchArgument(
            'framerate', default_value='30',
            description='Capture framerate.'
        ),
        DeclareLaunchArgument(
            'flip_method', default_value='0',
            description='nvvidconv flip method (0=none, 2=rotate-180).'
        ),
        DeclareLaunchArgument(
            'left_camera_info_path',
            default_value=default_left_cal,
            description='Path to left camera calibration YAML.'
        ),
        DeclareLaunchArgument(
            'right_camera_info_path',
            default_value=default_right_cal,
            description='Path to right camera calibration YAML.'
        ),
    ]

    gstreamer_camera_node = Node(
        package='orion_camera',
        executable='gstreamer_camera_node',
        name='gstreamer_dual_camera',
        output='screen',
        parameters=[{
            'capture_width': LaunchConfiguration('capture_width'),
            'capture_height': LaunchConfiguration('capture_height'),
            'framerate': LaunchConfiguration('framerate'),
            'flip_method': LaunchConfiguration('flip_method'),
            'left_camera_info_path': LaunchConfiguration('left_camera_info_path'),
            'right_camera_info_path': LaunchConfiguration('right_camera_info_path'),
        }],
    )

    return LaunchDescription(launch_args + [gstreamer_camera_node])
