#!/bin/bash
# Launch ROS2-Gazebo Camera Bridge for X500 mono camera

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Starting ROS2-Gazebo Camera Bridge..."
echo "Bridging camera topics from Gazebo to ROS2"

# Source ROS2 environment
source /opt/ros/humble/setup.bash
source ../ws_ros2/install/setup.bash

# Bridge camera image and camera info topics
echo "→ Bridging /imager topic to ROS2..."
ros2 run ros_gz_bridge parameter_bridge /imager@sensor_msgs/msg/Image@ignition.msgs.Image /imager/camera_info@sensor_msgs/msg/CameraInfo@ignition.msgs.CameraInfo --ros-args --remap /imager:=/camera --remap /imager/camera_info:=/camera_info