#!/bin/bash
# Launch multi-drone simulation in separate terminals for live monitoring

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the repository root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set paths
PX4_DIR="$REPO_ROOT/external/PX4-Autopilot"
MICRO_XRCE_AGENT="$REPO_ROOT/external/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent"
WS_ROS2="$REPO_ROOT/ws_ros2"

echo -e "${GREEN}=== Multi-Drone Simulation Launcher ===${NC}"
echo -e "${YELLOW}Repository root: $REPO_ROOT${NC}"
echo -e "${YELLOW}PX4 directory: $PX4_DIR${NC}"
echo -e "${YELLOW}Workspace: $WS_ROS2${NC}"

# Check if required directories exist
if [ ! -d "$PX4_DIR" ]; then
    echo -e "${RED}Error: PX4 directory not found at $PX4_DIR${NC}"
    exit 1
fi

if [ ! -f "$MICRO_XRCE_AGENT" ]; then
    echo -e "${RED}Error: MicroXRCEAgent not found at $MICRO_XRCE_AGENT${NC}"
    exit 1
fi

# Function to open a new terminal with a command
open_terminal() {
    local title="$1"
    local command="$2"
    local color="$3"

    # Try different terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$title" -- bash -c "$command; echo -e '${color}[Process exited. Press Enter to close]${NC}'; read"
    elif command -v xterm &> /dev/null; then
        xterm -title "$title" -e bash -c "$command; echo -e '${color}[Process exited. Press Enter to close]${NC}'; read" &
    elif command -v konsole &> /dev/null; then
        konsole --new-tab --title "$title" -e bash -c "$command; echo -e '${color}[Process exited. Press Enter to close]${NC}'; read" &
    elif command -v terminator &> /dev/null; then
        terminator --new-window --title="$title" -e bash -c "$command; echo -e '${color}[Process exited. Press Enter to close]${NC}'; read" &
    else
        echo -e "${RED}Error: No supported terminal emulator found (gnome-terminal, xterm, konsole, or terminator)${NC}"
        return 1
    fi
}

# Kill any existing processes
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -f px4
pkill -f MicroXRCEAgent
pkill -f gz
sleep 2

# Terminal 1: MicroXRCE Agent (for both drones)
echo -e "${BLUE}Starting Terminal 1: MicroXRCE Agent...${NC}"
AGENT_CMD="echo -e '${GREEN}=== MicroXRCE Agent ===${NC}'; \
echo 'Starting agent on UDP ports 8888 and 8889 for both drones...'; \
$MICRO_XRCE_AGENT udp4 -p 8888 & \
AGENT1_PID=\$!; \
sleep 1; \
$MICRO_XRCE_AGENT udp4 -p 8889 & \
AGENT2_PID=\$!; \
echo 'Both agents started. Press Ctrl+C to stop.'; \
wait \$AGENT1_PID \$AGENT2_PID"
open_terminal "MicroXRCE Agent" "$AGENT_CMD" "$GREEN"

# Wait for agent to start
sleep 3

# Terminal 2: Ally Drone (Instance 0)
echo -e "${BLUE}Starting Terminal 2: Ally Drone (Instance 0)...${NC}"
ALLY_CMD="echo -e '${GREEN}=== Ally Drone (Instance 0) ===${NC}'; \
echo 'Starting PX4 instance 0 with camera model...'; \
export LIBGL_ALWAYS_SOFTWARE=1; \
cd $PX4_DIR && \
mkdir -p $PX4_DIR/build/px4_sitl_default/instance_0 && \
cd $PX4_DIR/build/px4_sitl_default/instance_0 && \
export PX4_SYS_AUTOSTART=4001; \
export PX4_GZ_MODEL_POSE='0,2,0,0,0,4.71'; \
export PX4_SIM_MODEL=gz_x500_mono_cam; \
export PX4_INSTANCE=0; \
export MAV_BROADCAST=1; \
export PX4_MICRODDS_NS='px4_0'; \
export UXRCE_DDS_UDP_PORT=8888; \
$PX4_DIR/build/px4_sitl_default/bin/px4 -i 0"
open_terminal "Ally Drone (Instance 0)" "$ALLY_CMD" "$BLUE"

# Wait for Gazebo to start
echo -e "${YELLOW}Waiting for Gazebo to initialize...${NC}"
sleep 15

# Terminal 3: Enemy Drone (Instance 1)
echo -e "${BLUE}Starting Terminal 3: Enemy Drone (Instance 1)...${NC}"
ENEMY_CMD="echo -e '${RED}=== Enemy Drone (Instance 1) ===${NC}'; \
echo 'Starting PX4 instance 1...'; \
export LIBGL_ALWAYS_SOFTWARE=1; \
cd $PX4_DIR && \
mkdir -p $PX4_DIR/build/px4_sitl_default/instance_1 && \
cd $PX4_DIR/build/px4_sitl_default/instance_1 && \
PX4_GZ_WORLD=default \
PX4_GZ_STANDALONE=1 \
PX4_GZ_MODEL=x500_1 \
PX4_SYS_AUTOSTART=4001 \
PX4_GZ_MODEL_POSE='0,-2,0,0,0,0' \
PX4_SIM_MODEL=gz_x500 \
PX4_MICRODDS_NS='px4_1' \
UXRCE_DDS_UDP_PORT=8889 \
$PX4_DIR/build/px4_sitl_default/bin/px4 -i 1"
open_terminal "Enemy Drone (Instance 1)" "$ENEMY_CMD" "$RED"

# Wait for second drone to initialize
sleep 5

# Terminal 4: Camera Bridge
echo -e "${BLUE}Starting Terminal 4: Camera Bridge...${NC}"
BRIDGE_CMD="echo -e '${YELLOW}=== Camera Bridge ===${NC}'; \
echo 'Starting ROS2 camera bridge...'; \
source /opt/ros/humble/setup.bash; \
source $WS_ROS2/install/setup.bash; \
export LIBGL_ALWAYS_SOFTWARE=1; \
ros2 run ros_gz_bridge parameter_bridge \
/world/default/model/x500_mono_cam_0/link/camera_link/sensor/imager/image@sensor_msgs/msg/Image@gz.msgs.Image \
/world/default/model/x500_mono_cam_0/link/camera_link/sensor/imager/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo \
--ros-args \
-r /world/default/model/x500_mono_cam_0/link/camera_link/sensor/imager/image:=/camera/image \
-r /world/default/model/x500_mono_cam_0/link/camera_link/sensor/imager/camera_info:=/camera/camera_info"
open_terminal "Camera Bridge" "$BRIDGE_CMD" "$YELLOW"

# # Terminal 5: Camera Viewer
# echo -e "${BLUE}Starting Terminal 5: Camera Viewer...${NC}"
# VIEWER_CMD="echo -e '${GREEN}=== Camera Viewer ===${NC}'; \
# echo 'Starting RQT Image View...'; \
# source /opt/ros/humble/setup.bash; \
# source $WS_ROS2/install/setup.bash; \
# export LIBGL_ALWAYS_SOFTWARE=1; \
# ros2 run rqt_image_view rqt_image_view"
# open_terminal "Camera Viewer" "$VIEWER_CMD" "$GREEN"

# Terminal 6: Enemy Movement Control (waits for user)
echo -e "${BLUE}Starting Terminal 6: Enemy Movement Control...${NC}"
ENEMY_CONTROL_CMD="echo -e '${RED}=== Enemy Movement Control ===${NC}'; \
echo -e '${YELLOW}Ready to start enemy offboard control.${NC}'; \
echo -e '${GREEN}Press ENTER when ready to launch enemy movement...${NC}'; \
read; \
echo 'Starting enemy offboard control...'; \
source /opt/ros/humble/setup.bash; \
source $WS_ROS2/install/setup.bash; \
export LIBGL_ALWAYS_SOFTWARE=1; \
cd $WS_ROS2; \
ros2 run multi_drone_sim enemy_offboard_control"
open_terminal "Enemy Movement Control" "$ENEMY_CONTROL_CMD" "$RED"

echo -e "${GREEN}=== All terminals launched ===${NC}"
echo -e "${YELLOW}Terminal Summary:${NC}"
echo -e "  1. ${GREEN}MicroXRCE Agent${NC} - UDP ports 8888 (drone 0) and 8889 (drone 1)"
echo -e "  2. ${BLUE}Ally Drone${NC} - Instance 0 with camera"
echo -e "  3. ${RED}Enemy Drone${NC} - Instance 1"
echo -e "  4. ${YELLOW}Camera Bridge${NC} - ROS2 topic bridge"
echo -e "  5. ${GREEN}Camera Viewer${NC} - RQT Image View"
echo -e "  6. ${RED}Enemy Movement${NC} - Press ENTER in that terminal to start"
echo ""
