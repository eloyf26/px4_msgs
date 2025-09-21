#!/bin/bash
# Launch PX4 ROS COM offboard control example

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../ws_ros2"

source /opt/ros/humble/setup.bash
source install/setup.bash

echo "Starting PX4 ROS COM Offboard Control..."
echo "Make sure PX4 SITL and MicroXRCE Agent are running!"
ros2 run px4_ros_com offboard_control.py