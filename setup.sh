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

# 5. Clean all Gazebo installations (including Fortress)
echo "→ Removing all Gazebo installations (including Fortress)..."
sudo apt list --installed | grep -E 'gazebo|gz-|ignition-' | awk -F/ '{print $1}' | xargs -r sudo apt remove -y
sudo apt autoremove -y || true
echo "✓ All Gazebo installations removed"

# 2. Install PX4 Toolchain (includes gazebo harmonic)
echo "→ Installing PX4 Toolchain with gazebo harmonic simulator..."
cd external/PX4-Autopilot
bash ./Tools/setup/ubuntu.sh
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

# 4. Build MicroXRCE-DDS-Agent
echo "→ Building MicroXRCE-DDS-Agent..."
cd external/Micro-XRCE-DDS-Agent
mkdir -p build
cd build
cmake ..
make -j$(nproc)
cd "$SCRIPT_DIR"

# 6. Install ROS2 Gazebo Bridge package
echo "→ Installing ROS2 Bridge for Gazebo Harmonic package from source (humble branch)..."
sudo sh -c 'echo "deb [arch=$(dpkg --print-architecture)] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo apt-get update
sudo apt install ros-humble-ros-gz

# 7. Build ROS2 workspace
echo "→ Installing ROS2 build tools..."
sudo apt install -y \
    python3-colcon-common-extensions \
    ros-humble-rosidl-default-generators \
    ros-humble-ament-cmake \
    ros-humble-ament-cmake-cppcheck \
    ros-humble-ament-cmake-cpplint \
    ros-humble-ament-cmake-flake8 \
    ros-humble-ament-cmake-pep257 \
    ros-humble-ament-cmake-uncrustify \
    ros-humble-ament-lint-auto \
    ros-humble-ament-lint-common
echo "✓ ROS2 build tools installed"

echo "→ Building ROS2 packages..."
cd ws_ros2
source /opt/ros/humble/setup.bash

# Build in correct order
colcon build --packages-select halcon1_msgs
colcon build --packages-select px4_msgs px4_ros_com
colcon build --packages-select halcon1_detection halcon1_tracking halcon1_prediction halcon1_interception
colcon build --packages-select halcon1_bringup px4_offboard

cd "$SCRIPT_DIR"

# 8. Make all scripts executable
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
echo ""
