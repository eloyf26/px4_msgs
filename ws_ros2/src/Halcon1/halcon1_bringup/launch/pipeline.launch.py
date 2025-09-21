from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='halcon1_detection',
            executable='detection_node',
            name='detection_node'
        ),
        Node(
            package='halcon1_tracking',
            executable='tracking_node',
            name='tracking_node'
        ),
        Node(
            package='halcon1_prediction',
            executable='prediction_node',
            name='prediction_node'
        ),
        Node(
            package='halcon1_interception',
            executable='interception_node',
            name='interception_node'
        ),
    ])