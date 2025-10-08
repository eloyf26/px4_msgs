from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition
from launch_ros.actions import Node

def generate_launch_description():
    # Declare launch arguments
    debug_arg = DeclareLaunchArgument(
        'debug',
        default_value='false',
        description='Enable debug mode for all nodes'
    )

    skip_detection_arg = DeclareLaunchArgument(
        'skip_detection',
        default_value='false',
        description='Skip launching the detection node'
    )

    skip_tracking_arg = DeclareLaunchArgument(
        'skip_tracking',
        default_value='false',
        description='Skip launching the tracking node'
    )

    skip_guidance_arg = DeclareLaunchArgument(
        'skip_guidance',
        default_value='false',
        description='Skip launching the guidance node'
    )

    # Get launch configurations
    debug = LaunchConfiguration('debug')
    skip_detection = LaunchConfiguration('skip_detection')
    skip_tracking = LaunchConfiguration('skip_tracking')
    skip_guidance = LaunchConfiguration('skip_guidance')

    return LaunchDescription([
        debug_arg,
        skip_detection_arg,
        skip_tracking_arg,
        skip_guidance_arg,
        Node(
            package='detection',
            executable='detection_node',
            name='detection_node',
            output='screen',
            parameters=[{
                'use_sim_time': False,  # Set to False for now, True only with Gazebo running
                'debug': debug
            }],
            condition=IfCondition(PythonExpression(['not ', skip_detection]))
        ),
        Node(
            package='tracking',
            executable='tracking_node',
            name='tracking_node',
            output='screen',
            parameters=[{
                'use_sim_time': False,  # Set to False for now, True only with Gazebo running
                'debug': debug
            }],
            condition=IfCondition(PythonExpression(['not ', skip_tracking]))
        ),
        Node(
            package='guidance',
            executable='guidance_node',
            name='guidance_node',
            output='screen',
            parameters=[{
                'use_sim_time': False,  # Set to False for now, True only with Gazebo running
                'debug': debug
            }],
            condition=IfCondition(PythonExpression(['not ', skip_guidance]))
        ),
    ])