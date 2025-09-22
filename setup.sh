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
    make px4_sitl_default
    cd "$SCRIPT_DIR"
fi

# 4. Install PX4 Toolchain (with Gazebo Harmonic simulator)
echo "→ Installing PX4 Toolchain with Gazebo Harmonic..."
cd external/PX4-Autopilot
bash ./Tools/setup/ubuntu.sh
cd "$SCRIPT_DIR"

# 5. Install ROS2 Gazebo Harmonic Bridge packages
echo "→ Installing ROS2 Gazebo Harmonic Bridge packages..."
sudo apt update
sudo apt install -y ros-humble-ros-gzharmonic ros-humble-ros-gz-image ros-humble-ros-gz-bridge
echo "✓ ROS2 Gazebo Harmonic bridge packages installed"

# 6. Build ROS2 workspace
echo "→ Building ROS2 packages..."
cd ws_ros2
source /opt/ros/humble/setup.bash

# Build in correct order
colcon build --packages-select halcon1_msgs
colcon build --packages-select px4_msgs px4_ros_com
colcon build --packages-select halcon1_detection halcon1_tracking halcon1_prediction halcon1_interception
colcon build --packages-select halcon1_bringup px4_offboard

cd "$SCRIPT_DIR"

# 7. Make all scripts executable
echo "→ Making scripts executable..."
chmod +x scripts/*.sh
echo "✓ All scripts are now executable"

echo "=== Setup Complete ==="
echo ""
echo "To use the system with camera:"
echo "  1. Terminal 1: ./scripts/launch_px4.sh          # PX4 SITL with x500_mono_cam"
echo "  2. Terminal 2: ./scripts/launch_agent.sh        # MicroXRCE Agent (bridge PX4 → ROS2)"
echo "  3. Terminal 3: ./scripts/launch_camera_bridge.sh # Camera bridge (Gazebo → ROS2)"
echo "  4. Terminal 4: ./scripts/launch_halcon1.sh       # Halcon1 Pipeline"
echo ""
echo "Camera feed will be available on ROS2 topics:"
echo "  /camera       - Camera images (sensor_msgs/Image)"
echo "  /camera_info  - Camera calibration info"
echo ""
echo "Source ROS2 workspace:"
echo "  source $SCRIPT_DIR/ws_ros2/install/setup.bash"