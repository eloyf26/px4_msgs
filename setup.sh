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

# 5. Install ROS2 Humble
echo "→ Installing ROS2 Humble..."
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install -y curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y ros-humble-desktop
echo "✓ ROS2 Humble installed"

# 6. Initialize rosdep and setup rules for Gazebo Harmonic
echo "→ Setting up rosdep rules for Gazebo Harmonic..."
sudo mkdir -p /etc/ros/rosdep/sources.list.d
sudo bash -c 'wget https://raw.githubusercontent.com/osrf/osrf-rosdep/master/gz/00-gazebo.list -O /etc/ros/rosdep/sources.list.d/00-gazebo.list'
sudo apt update
sudo apt install python3-rosdep -y
sudo rosdep init || true  # Don't fail if already initialized
rosdep update
rosdep resolve gz-harmonic
echo "✓ Rosdep rules for Gazebo Harmonic installed"

# 7. Clone ros_gz from source (humble branch)
echo "→ Cloning ros_gz from source (humble branch)..."
cd ws_ros2/src
git clone https://github.com/gazebosim/ros_gz.git -b humble
export GZ_VERSION=humble # Required for building ros_gz in step 9
cd "$SCRIPT_DIR"
echo "✓ ros_gz cloned from humble branch"

# 8. Build ROS2 workspace
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

# 8. Build in correct order
echo "→ Building packages in correct order..."
colcon build --packages-select ros_gz
colcon build --packages-select halcon1_msgs
colcon build --packages-select px4_msgs px4_ros_com
colcon build --packages-select halcon1_detection halcon1_tracking halcon1_prediction halcon1_interception
colcon build --packages-select halcon1_bringup px4_offboard

cd "$SCRIPT_DIR"

# 9. Make all scripts executable
echo "→ Making scripts executable..."
chmod +x scripts/*.sh
chmod +x rebuild.sh
echo "✓ All scripts are now executable"

echo "=== Setup Complete ==="
echo ""
echo "🚀 Quick Start Options:"
echo ""
echo "Option 1 - Launch Everything (Recommended):"
echo "  ./launch_all.sh                                 # Launches all components automatically"
echo ""
echo "Option 2 - Manual Launch (4 terminals):"
echo "  1. Terminal 1: ./scripts/launch_px4.sh          # PX4 SITL with x500_mono_cam"
echo "  2. Terminal 2: ./scripts/launch_agent.sh        # MicroXRCE Agent (bridge PX4 → ROS2)"
echo "  3. Terminal 3: ./scripts/launch_camera_bridge.sh # Camera bridge (Gazebo → ROS2)"
echo "  4. Terminal 4: ./scripts/launch_halcon1.sh       # Halcon1 ROS2 nodes Pipeline"
echo ""
echo "🔧 Development Tools:"
echo "  ./rebuild.sh                                     # Quick rebuild after code changes"
echo ""
echo "📊 Available ROS2 Topics:"
echo "  /camera/image       - Camera images (sensor_msgs/Image)"
echo "  /camera/camera_info - Camera calibration info"
echo "  /enemy/detection    - Target detections @ 10Hz"
echo "  /enemy/tracked      - Target tracking @ 10Hz"
echo "  /enemy/predicted    - Trajectory predictions @ 10Hz"
echo "  /interception/command - Interception commands @ 10Hz"
echo ""
echo "Source ROS2 workspace in new terminals:"
echo "  source $SCRIPT_DIR/ws_ros2/install/setup.bash"
echo ""
