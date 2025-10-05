#!/bin/bash
# Validation script for Halcon1 system setup
# Checks all dependencies and provides helpful feedback

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}=== Halcon1 System Validation ===${NC}"
echo ""

# Track overall status
ALL_GOOD=true

# Function to check and report status
check_status() {
    local name="$1"
    local check_cmd="$2"
    local error_msg="$3"
    local fix_msg="$4"
    local optional="${5:-false}"

    if eval "$check_cmd" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $name"
        return 0
    else
        if [ "$optional" = true ]; then
            echo -e "  ${YELLOW}○${NC} $name (optional)"
        else
            echo -e "  ${RED}✗${NC} $name"
            ALL_GOOD=false
        fi
        if [ -n "$error_msg" ]; then
            echo -e "    ${YELLOW}Issue: $error_msg${NC}"
        fi
        if [ -n "$fix_msg" ]; then
            echo -e "    ${BLUE}Fix: $fix_msg${NC}"
        fi
        return 1
    fi
}

# Core Dependencies
echo -e "${BLUE}Core Dependencies:${NC}"
check_status "ROS2 Humble installed" \
    "test -f /opt/ros/humble/setup.bash" \
    "ROS2 Humble not found" \
    "Install via: sudo apt install ros-humble-desktop"

check_status "Python 3 installed" \
    "command -v python3" \
    "Python 3 not found" \
    "Install via: sudo apt install python3"

check_status "pip3 installed" \
    "command -v pip3" \
    "pip3 not found" \
    "Install via: sudo apt install python3-pip"

check_status "colcon build tools" \
    "command -v colcon" \
    "colcon not found" \
    "Install via: sudo apt install python3-colcon-common-extensions"

echo ""

# PX4 Dependencies
echo -e "${BLUE}PX4 SITL:${NC}"
check_status "PX4 repository cloned" \
    "test -d $REPO_ROOT/external/PX4-Autopilot" \
    "PX4-Autopilot directory not found" \
    "Run: git submodule update --init --recursive"

check_status "PX4 SITL binary built" \
    "test -f $REPO_ROOT/external/PX4-Autopilot/build/px4_sitl_default/bin/px4" \
    "PX4 SITL not compiled" \
    "Run: cd external/PX4-Autopilot && make px4_sitl_default"

check_status "MicroXRCE-DDS Agent built" \
    "test -f $REPO_ROOT/external/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent" \
    "MicroXRCE Agent not compiled" \
    "Run: cd external/Micro-XRCE-DDS-Agent/build && cmake .. && make"

echo ""

# Gazebo Dependencies (optional)
echo -e "${BLUE}Gazebo Harmonic (optional):${NC}"
check_status "Gazebo Harmonic installed" \
    "command -v gz" \
    "Gazebo Harmonic not found" \
    "Installed automatically by PX4 toolchain setup" \
    true

check_status "ros_gz packages built" \
    "test -d $REPO_ROOT/ws_ros2/install/ros_gz" \
    "ros_gz not built" \
    "Run: cd ws_ros2 && colcon build --packages-select ros_gz" \
    true

echo ""

# AirSim Dependencies (optional)
echo -e "${BLUE}AirSim (optional):${NC}"
check_status "AirSim Python package" \
    "python3 -c 'import airsim'" \
    "AirSim Python package not installed" \
    "Run: pip3 install airsim" \
    true

check_status "msgpack-rpc-python package" \
    "python3 -c 'import msgpackrpc'" \
    "msgpack-rpc-python not installed" \
    "Run: pip3 install msgpack-rpc-python" \
    true

check_status "camera_bridge built" \
    "test -d $REPO_ROOT/ws_ros2/install/camera_bridge" \
    "camera_bridge not built" \
    "Run: ./setup.sh --airsim" \
    true

check_status "viz_translator built" \
    "test -d $REPO_ROOT/ws_ros2/install/viz_translator" \
    "viz_translator not built" \
    "Run: ./setup.sh --airsim" \
    true

check_status "AirSim settings.json configured" \
    "test -f $HOME/Documents/AirSim/settings.json" \
    "AirSim settings.json not found" \
    "Run: ./setup.sh --airsim (auto-copies config)" \
    true

check_status "AirSim environment downloaded" \
    "test -d $HOME/AirSimEnvironments" \
    "No AirSim environment found" \
    "Run: ./scripts/install_airsim_env.sh --blocks" \
    true

echo ""

# ROS2 Workspace
echo -e "${BLUE}ROS2 Workspace:${NC}"
check_status "ROS2 workspace built" \
    "test -f $REPO_ROOT/ws_ros2/install/setup.bash" \
    "Workspace not built" \
    "Run: cd ws_ros2 && colcon build"

check_status "msgs package" \
    "test -d $REPO_ROOT/ws_ros2/install/msgs" \
    "msgs not built" \
    "Run: cd ws_ros2 && colcon build --packages-select msgs"

check_status "detection package" \
    "test -d $REPO_ROOT/ws_ros2/install/detection" \
    "detection not built" \
    "Run: cd ws_ros2 && colcon build --packages-select detection"

check_status "tracking package" \
    "test -d $REPO_ROOT/ws_ros2/install/tracking" \
    "tracking not built" \
    "Run: cd ws_ros2 && colcon build --packages-select tracking"

check_status "guidance package" \
    "test -d $REPO_ROOT/ws_ros2/install/guidance" \
    "guidance not built" \
    "Run: cd ws_ros2 && colcon build --packages-select guidance"

check_status "utils package" \
    "test -d $REPO_ROOT/ws_ros2/install/utils" \
    "utils not built" \
    "Run: cd ws_ros2 && colcon build --packages-select utils"

check_status "common_types package" \
    "test -d $REPO_ROOT/ws_ros2/install/common_types" \
    "common_types not built" \
    "Run: cd ws_ros2 && colcon build --packages-select common_types"

check_status "px4_msgs package" \
    "test -d $REPO_ROOT/ws_ros2/install/px4_msgs" \
    "px4_msgs not built" \
    "Run: cd ws_ros2 && colcon build --packages-select px4_msgs"

echo ""

# Python Dependencies
echo -e "${BLUE}Python Dependencies:${NC}"
check_status "ultralytics (YOLO)" \
    "python3 -c 'import ultralytics'" \
    "ultralytics not installed" \
    "Run: pip3 install -r requirements.txt"

check_status "PyTorch (torch)" \
    "python3 -c 'import torch'" \
    "PyTorch not installed" \
    "Run: pip3 install -r requirements.txt"

check_status "OpenCV (cv2)" \
    "python3 -c 'import cv2'" \
    "OpenCV not installed" \
    "Run: pip3 install -r requirements.txt"

check_status "NumPy" \
    "python3 -c 'import numpy'" \
    "NumPy not installed" \
    "Run: pip3 install -r requirements.txt"

check_status "SciPy" \
    "python3 -c 'import scipy'" \
    "SciPy not installed" \
    "Run: pip3 install -r requirements.txt"

check_status "PyYAML" \
    "python3 -c 'import yaml'" \
    "PyYAML not installed" \
    "Run: pip3 install -r requirements.txt"

echo ""

# Scripts Executable
echo -e "${BLUE}Scripts:${NC}"
check_status "launch_px4.sh executable" \
    "test -x $REPO_ROOT/scripts/launch_px4.sh" \
    "Script not executable" \
    "Run: chmod +x scripts/launch_px4.sh"

check_status "launch_agent.sh executable" \
    "test -x $REPO_ROOT/scripts/launch_agent.sh" \
    "Script not executable" \
    "Run: chmod +x scripts/launch_agent.sh"

check_status "launch_airsim.sh executable" \
    "test -x $REPO_ROOT/scripts/launch_airsim.sh" \
    "Script not executable" \
    "Run: chmod +x scripts/launch_airsim.sh" \
    true

check_status "install_airsim_env.sh executable" \
    "test -x $REPO_ROOT/scripts/install_airsim_env.sh" \
    "Script not executable" \
    "Run: chmod +x scripts/install_airsim_env.sh" \
    true

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Final summary
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All required components are installed and configured!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  ${GREEN}Gazebo:${NC} ./scripts/launch_multi_terminal.sh"
    echo -e "  ${GREEN}AirSim:${NC} ./scripts/launch_airsim.sh"
else
    echo -e "${YELLOW}⚠ Some required components are missing or not configured${NC}"
    echo ""
    echo -e "${BLUE}To fix issues:${NC}"
    echo -e "  Run: ${GREEN}./setup.sh --full${NC}     # Install everything"
    echo -e "  Or:  ${GREEN}./setup.sh --gazebo${NC}  # Install Gazebo only"
    echo -e "  Or:  ${GREEN}./setup.sh --airsim${NC}  # Install AirSim only"
    echo ""
    exit 1
fi

echo ""
