#!/usr/bin/env python3
"""
Simplified launch file for two-drone simulation.
One regular X500, one with camera.
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    """Generate launch description for two-drone simulation."""

    # Get the repository root directory (halcon1-system)
    # The launch file is in ws_ros2/install/multi_drone_sim/share/multi_drone_sim/launch/two_drones.launch.py
    repo_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../../..')
    repo_root = os.path.abspath(repo_root)

    px4_dir = os.path.join(repo_root, 'external/PX4-Autopilot')
    micro_xrce_agent = os.path.join(repo_root, 'external/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent')

    return LaunchDescription([
        # Start MicroXRCEAgent
        ExecuteProcess(
            cmd=[micro_xrce_agent, 'udp4', '-p', '8888'],
            output='screen',
            name='micro_xrce_agent'
        ),

        # Wait for agent
        TimerAction(
            period=2.0,
            actions=[
                # Drone 1 - Regular X500 (starts Gazebo)
                ExecuteProcess(
                    cmd=[px4_dir + '/build/px4_sitl_default/bin/px4', '-i', '0'],
                    cwd=px4_dir,
                    output='screen',
                    name='px4_drone_1',
                    env={
                        'PX4_SYS_AUTOSTART': '4001',
                        'PX4_SIM_MODEL': 'gz_x500',
                        'PX4_GZ_MODEL_POSE': '0,0',
                    }
                ),
            ]
        ),

        # Wait for Gazebo to start
        TimerAction(
            period=8.0,
            actions=[
                # Drone 2 - X500 with camera
                ExecuteProcess(
                    cmd=[px4_dir + '/build/px4_sitl_default/bin/px4', '-i', '1'],
                    cwd=px4_dir,
                    output='screen',
                    name='px4_drone_2',
                    env={
                        'PX4_SYS_AUTOSTART': '4001',
                        'PX4_SIM_MODEL': 'gz_x500_mono_cam',
                        'PX4_GZ_STANDALONE': '1',
                        'PX4_GZ_MODEL_POSE': '-3,0',
                    }
                ),

                # Camera bridge for drone 2 (x500_mono_cam_1)
                Node(
                    package='ros_gz_bridge',
                    executable='parameter_bridge',
                    name='camera_bridge',
                    output='screen',
                    arguments=[
                        '/world/default/model/x500_mono_cam_1/link/camera_link/sensor/imager/image@sensor_msgs/msg/Image@gz.msgs.Image',
                        '/world/default/model/x500_mono_cam_1/link/camera_link/sensor/imager/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
                    ],
                    remappings=[
                        ('/world/default/model/x500_mono_cam_1/link/camera_link/sensor/imager/image', '/px4_1/camera/image'),
                        ('/world/default/model/x500_mono_cam_1/link/camera_link/sensor/imager/camera_info', '/px4_1/camera/camera_info'),
                    ]
                ),
            ]
        ),
    ])