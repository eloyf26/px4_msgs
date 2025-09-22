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

# 2. Install PX4 Toolchain (without simulator to avoid conflicts)
echo "→ Installing PX4 Toolchain without simulator..."
cd external/PX4-Autopilot
bash ./Tools/setup/ubuntu.sh --no-sim-tools
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

# 5. Clean and install Gazebo Fortress (compatible with ROS2 Humble)
echo "→ Cleaning any existing Gazebo installations except Gazebo Fortress..."
sudo apt list --installed | grep -E 'gazebo|gz-|ignition-' | grep -v 'gz-fortress' | awk -F/ '{print $1}' | xargs -r sudo apt remove -y
sudo apt autoremove -y || true
echo "✓ Existing Gazebo installations (except Fortress) cleaned"

echo "→ Installing Gazebo Fortress..."
sudo apt update
sudo apt install -y lsb-release wget gnupg
sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt update
sudo apt install -y gz-fortress
echo "✓ Gazebo Fortress installed"

# 6. Install ROS2 Gazebo Bridge package
echo "→ Setting up ROS2 repository for ros-gz packages..."
# Ensure ROS2 repository is configured
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb [arch=$(dpkg --print-architecture)] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'
sudo apt update

echo "→ Installing ROS2 Gazebo Bridge package..."
sudo apt install -y ros-humble-ros-gz
echo "✓ ROS2 Gazebo bridge package installed"

# 7. Build ROS2 workspace
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
