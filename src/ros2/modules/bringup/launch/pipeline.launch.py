from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Declare launch arguments
    debug_arg = DeclareLaunchArgument(
        'debug',
        default_value='false',
        description='Enable debug mode for all nodes'
    )

    # Get launch configurations
    debug = LaunchConfiguration('debug')

    return LaunchDescription([
        debug_arg,
        Node(
            package='detection',
            executable='detection_node',
            name='detection_node',
            output='screen',
            parameters=[{
                'use_sim_time': False,  # Set to False for now, True only with Gazebo running
                'debug': debug
            }]
        ),
        Node(
            package='tracking',
            executable='tracking_node',
            name='tracking_node',
            output='screen',
            parameters=[{
                'use_sim_time': False,  # Set to False for now, True only with Gazebo running
                'debug': debug
            }]
        ),
        Node(
            package='guidance',
            executable='guidance_node',
            name='guidance_node',
            output='screen',
            parameters=[{
                'use_sim_time': False,  # Set to False for now, True only with Gazebo running
                'debug': debug
            }]
        ),
    ])