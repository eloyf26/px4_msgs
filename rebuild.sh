#!/bin/bash

# Halcon1 System Rebuild Script
# This system rebuilds all components from scratch. It is meant to update the built packages
# that are then launched using the launch scripts in the scripts/ folder.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "→ Building ROS2 packages..."
cd ws_ros2
source /opt/ros/humble/setup.bash

# Build in correct order
echo "→ Building packages in correct order..."
colcon build --packages-select ros_gz
colcon build --packages-select halcon1_msgs
colcon build --packages-select halcon1_types
colcon build --packages-select px4_msgs px4_ros_com
colcon build --packages-select halcon1_detection halcon1_tracking halcon1_guidance
colcon build --packages-select halcon1_bringup px4_offboard

# Return to original directory
cd "$SCRIPT_DIR"

echo "✓ Rebuild complete"
echo ""
echo "🚀 Quick Start Options:"
echo ""
echo "Source ROS2 workspace in new terminals:"
echo "  source $SCRIPT_DIR/ws_ros2/install/setup.bash"
echo ""