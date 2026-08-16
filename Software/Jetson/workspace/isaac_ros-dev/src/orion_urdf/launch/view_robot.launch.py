from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg = get_package_share_directory('orion_urdf')

    use_gui = DeclareLaunchArgument(
        'use_gui',
        default_value='false',
        description='Use joint_state_publisher_gui to move joints'
    )

    urdf_file = PathJoinSubstitution([pkg, 'urdf', 'robot_description.urdf']) 
    robot_description = Command(['cat ', urdf_file])

    # OPTION A: Manual Slider GUI (Runs ONLY when use_gui:=true)
    jsp_gui = Node(
        condition=IfCondition(LaunchConfiguration('use_gui')),
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        parameters=[{'rate': 30.0}],
        emulate_tty=True
    )

    # OPTION B: Standard Publisher listening to an external node
    jsp_standard = Node(
        condition=UnlessCondition(LaunchConfiguration('use_gui')),
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{
            'rate': 30.0,
            # 'source_list': ['/my_custom_node_joint_states'] # Listen to your custom node!
        }]
    )

    # Publishes TF from the URDF
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    # Opening RViz and give a default view
    # rviz = Node(
    #     package='rviz2',
    #     executable='rviz2',
    #     name='rviz2',
    #     arguments=['-d', PathJoinSubstitution([pkg, 'rviz', 'urdf_view.rviz'])],
    #     output='screen'
    # )

    return LaunchDescription([
        use_gui,
        jsp_gui,
        jsp_standard,
        rsp,
        # rviz
    ])
