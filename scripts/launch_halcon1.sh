#!/bin/bash
# Launch Halcon1 pipeline

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../ws_ros2"

source /opt/ros/humble/setup.bash
source install/setup.bash

echo "Starting Halcon1 pipeline..."
ros2 launch halcon1_bringup pipeline.launch.py