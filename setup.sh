#!/bin/bash

# Halcon1 System Setup Script
# This script initializes all dependencies and builds the complete system

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=== Halcon1 System Setup ==="

# 1. Initialize and update git submodules
echo "→ Initializing git submodules..."
git submodule update --init --recursive

# 2. Build MicroXRCE-DDS-Agent
echo "→ Building MicroXRCE-DDS-Agent..."
cd external/Micro-XRCE-DDS-Agent
mkdir -p build
cd build
cmake ..
make -j$(nproc)
cd "$SCRIPT_DIR"

# 3. Build PX4 (optional, takes time)
read -p "Build PX4 SITL? This will take 10-20 minutes (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Building PX4 SITL..."
    cd external/PX4-Autopilot
    make px4_sitl gz_x500
    cd "$SCRIPT_DIR"
fi

# 4. Build ROS2 workspace
echo "→ Building ROS2 packages..."
cd ws_ros2
source /opt/ros/humble/setup.bash

# Build in correct order
colcon build --packages-select halcon1_msgs
colcon build --packages-select px4_msgs px4_ros_com
colcon build --packages-select halcon1_detection halcon1_tracking halcon1_prediction halcon1_interception
colcon build --packages-select halcon1_bringup px4_offboard

echo "=== Setup Complete ==="
echo ""
echo "To use the system:"
echo "  1. Terminal 1: ./scripts/launch_px4.sh"
echo "  2. Terminal 2: ./scripts/launch_agent.sh"
echo "  3. Terminal 3: ./scripts/launch_halcon1.sh"
echo ""
echo "Source ROS2 workspace:"
echo "  source $SCRIPT_DIR/ws_ros2/install/setup.bash"