#!/bin/bash
# Launch multi-drone simulation

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../ws_ros2"
source /opt/ros/humble/setup.bash
source install/setup.bash
export LIBGL_ALWAYS_SOFTWARE=1
ros2 launch multi_drone_sim two_drones.launch.py