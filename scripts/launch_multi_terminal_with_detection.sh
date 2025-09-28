#!/bin/bash
# Launch multi-drone simulation with detection node in separate terminals for live monitoring

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse command line arguments
DEBUG_MODE=false
for arg in "$@"; do
    case $arg in
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        *)
            ;;
    esac
done

# Get the repository root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set paths
PX4_DIR="$REPO_ROOT/external/PX4-Autopilot"
MICRO_XRCE_AGENT="$REPO_ROOT/external/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent"
WS_ROS2="$REPO_ROOT/ws_ros2"

# ===== SIMULATION CONFIGURATION =====
# Gazebo world settings
GZ_WORLD="default"

# PX4 configuration
PX4_AUTOSTART="4001"
PX4_GZ_SIM_RENDER_ENGINE="ogre2"
export LIBGL_ALWAYS_SOFTWARE=1 # Software rendering for WSL/containers

# Drone configuration
ALLY_INSTANCE=0 # Do not change this if you want to use QGroundControl, the UDP port is assigned based on this value and QgroundControl fails to connect to other ports
ALLY_POSITION="0,2,0,0,0,4.71"  # x,y,z,roll,pitch,yaw (facing -90 deg)
ALLY_MODEL="x500_mono_cam"  # Using custom forward-facing camera model

ENEMY_INSTANCE=$((ALLY_INSTANCE + 1))
ENEMY_POSITION="0,-2,0,0,0,0"  # x,y,z,roll,pitch,yaw

# Camera configuration
GAZEBO_MODEL_NAME="${ALLY_MODEL}_${ALLY_INSTANCE}"

# ROS paths
ROS_SETUP="/opt/ros/humble/setup.bash"
WS_SETUP="$WS_ROS2/install/setup.bash"

echo -e "${GREEN}=== Multi-Drone Simulation Launcher with Detection ===${NC}"
echo -e "${CYAN}*** DETECTION MODULE INCLUDED ***${NC}"
echo -e "${YELLOW}Repository root: $REPO_ROOT${NC}"
echo -e "${YELLOW}PX4 directory: $PX4_DIR${NC}"
echo -e "${YELLOW}Workspace: $WS_ROS2${NC}"
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${MAGENTA}DEBUG MODE: Enabled - PX4 Debug Translator will be launched${NC}"
fi

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
pkill -f detection_node
sleep 2

# Terminal 1: MicroXRCE Agent (for all drones)
echo -e "${BLUE}Starting Terminal 1: MicroXRCE Agent...${NC}"
AGENT_CMD="echo -e '${GREEN}=== MicroXRCE Agent ===${NC}'; \
echo 'Starting agent on UDP port 8888 for all drones...'; \
$MICRO_XRCE_AGENT udp4 -p 8888"
open_terminal "MicroXRCE Agent" "$AGENT_CMD" "$GREEN"

# Wait for agent to start
sleep 3

# Terminal 2: Ally Drone (Instance 0) - First vehicle starts Gazebo
echo -e "${BLUE}Starting Terminal 2: Ally Drone (Instance $ALLY_INSTANCE)...${NC}"
ALLY_CMD="echo -e '${GREEN}=== Ally Drone (Instance $ALLY_INSTANCE) ===${NC}'; \
echo 'Starting PX4 instance $ALLY_INSTANCE with custom camera model (will start Gazebo)...'; \
cd $PX4_DIR && \
PX4_SYS_AUTOSTART=$PX4_AUTOSTART \
PX4_GZ_SIM_RENDER_ENGINE=$PX4_GZ_SIM_RENDER_ENGINE \
PX4_SIM_MODEL=$ALLY_MODEL \
PX4_GZ_WORLD=$GZ_WORLD \
PX4_GZ_MODEL_POSE='$ALLY_POSITION' \
./build/px4_sitl_default/bin/px4 -i $ALLY_INSTANCE"
open_terminal "Ally Drone (Instance $ALLY_INSTANCE)" "$ALLY_CMD" "$BLUE"

# Wait for Gazebo to start
echo -e "${YELLOW}Waiting for Gazebo to initialize...${NC}"
sleep 15

# Terminal 3: Enemy Drone (Instance 1) - Standalone mode
echo -e "${BLUE}Starting Terminal 3: Enemy Drone (Instance $ENEMY_INSTANCE)...${NC}"
ENEMY_CMD="echo -e '${RED}=== Enemy Drone (Instance $ENEMY_INSTANCE) ===${NC}'; \
echo 'Starting PX4 instance $ENEMY_INSTANCE in standalone mode...'; \
cd $PX4_DIR && \
PX4_GZ_STANDALONE=1 \
PX4_GZ_SIM_RENDER_ENGINE=$PX4_GZ_SIM_RENDER_ENGINE \
PX4_SYS_AUTOSTART=$PX4_AUTOSTART \
PX4_GZ_MODEL_POSE='$ENEMY_POSITION' \
PX4_GZ_WORLD=$GZ_WORLD \
PX4_SIM_MODEL=gz_x500 \
./build/px4_sitl_default/bin/px4 -i $ENEMY_INSTANCE"
open_terminal "Enemy Drone (Instance $ENEMY_INSTANCE)" "$ENEMY_CMD" "$RED"

# Wait for second drone to initialize
sleep 5

# Terminal 4: Camera Bridge
echo -e "${BLUE}Starting Terminal 4: Camera Bridge...${NC}"
BRIDGE_CMD="echo -e '${YELLOW}=== Camera Bridge ===${NC}'; \
echo 'Starting ROS2 camera bridge...'; \
source $ROS_SETUP; \
source $WS_SETUP; \
ros2 run ros_gz_bridge parameter_bridge \
/world/$GZ_WORLD/model/$GAZEBO_MODEL_NAME/link/camera_link/sensor/imager/image@sensor_msgs/msg/Image@gz.msgs.Image \
/world/$GZ_WORLD/model/$GAZEBO_MODEL_NAME/link/camera_link/sensor/imager/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo \
--ros-args \
-r /world/$GZ_WORLD/model/$GAZEBO_MODEL_NAME/link/camera_link/sensor/imager/image:=/camera/image \
-r /world/$GZ_WORLD/model/$GAZEBO_MODEL_NAME/link/camera_link/sensor/imager/camera_info:=/camera/camera_info"
open_terminal "Camera Bridge" "$BRIDGE_CMD" "$YELLOW"

# Terminal 5: Detection Node (NEW)
echo -e "${CYAN}Starting Terminal 5: Detection Node (YOLOv11n)...${NC}"
DETECTION_CMD="echo -e '${CYAN}=== Detection Node (YOLOv11n) ===${NC}'; \
echo -e '${YELLOW}Starting drone detection with YOLOv11n...${NC}'; \
echo ''; \
echo 'Detection outputs:'; \
echo '  - /enemy/detection: Bounding box coordinates'; \
echo '  - /debug/ally/detection_image: Annotated camera feed'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
echo -e '${GREEN}Detection node starting...${NC}'; \
ros2 run halcon1_detection detection_node"
open_terminal "Detection Node" "$DETECTION_CMD" "$CYAN"

# Terminal 6: RViz2 Visualization
echo -e "${BLUE}Starting Terminal 6: RViz2 Visualization...${NC}"
RVIZ_CMD="echo -e '${GREEN}=== RViz2 Visualization ===${NC}'; \
echo 'Starting RViz2 for trajectory and detection visualization...'; \
echo ''; \
echo -e '${CYAN}To view detection results:${NC}'; \
echo '  1. Add Image display'; \
echo '  2. Set topic to /debug/ally/detection_image'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
ros2 run rviz2 rviz2"
open_terminal "RViz2" "$RVIZ_CMD" "$GREEN"

# Terminal 7: Enemy Movement Control (waits for user)
echo -e "${BLUE}Starting Terminal 7: Enemy Movement Control...${NC}"
ENEMY_CONTROL_CMD="echo -e '${RED}=== Enemy Movement Control ===${NC}'; \
echo -e '${YELLOW}Ready to start enemy offboard control.${NC}'; \
echo -e '${GREEN}Press ENTER when ready to launch enemy movement...${NC}'; \
read; \
echo 'Starting enemy offboard control...'; \
source $ROS_SETUP; \
source $WS_SETUP; \
cd $WS_ROS2; \
ros2 run multi_drone_sim enemy_offboard_control"
open_terminal "Enemy Movement Control" "$ENEMY_CONTROL_CMD" "$RED"

# Terminal 8 (if debug mode): PX4 Debug Translator
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${BLUE}Starting Terminal 8: PX4 Debug Translator...${NC}"
    DEBUG_CMD="echo -e '${MAGENTA}=== PX4 Debug Translator ===${NC}'; \
    echo 'Translating PX4 topics to ROS2 standard types for visualization...'; \
    echo ''; \
    echo 'Available topics in RViz2:'; \
    echo '  /debug/ally/pose (PoseStamped)'; \
    echo '  /debug/ally/path (Path)'; \
    echo '  /debug/ally/setpoint (PoseStamped)'; \
    echo '  /debug/enemy/pose (PoseStamped)'; \
    echo '  /debug/enemy/path (Path)'; \
    echo '  /debug/enemy/setpoint (PoseStamped)'; \
    echo ''; \
    source $ROS_SETUP; \
    source $WS_SETUP; \
    ros2 run multi_drone_sim px4_debug_translator"
    open_terminal "PX4 Debug Translator" "$DEBUG_CMD" "$MAGENTA"
fi

echo -e "${GREEN}=== All terminals launched ===${NC}"
echo -e "${YELLOW}Terminal Summary:${NC}"
echo -e "  1. ${GREEN}MicroXRCE Agent${NC} - UDP port 8888 (all drones)"
echo -e "  2. ${BLUE}Ally Drone${NC} - Instance 0 with camera"
echo -e "  3. ${RED}Enemy Drone${NC} - Instance 1"
echo -e "  4. ${YELLOW}Camera Bridge${NC} - ROS2 topic bridge"
echo -e "  5. ${CYAN}Detection Node${NC} - YOLOv11n drone detection"
echo -e "  6. ${GREEN}RViz2${NC} - 3D visualization of trajectories and detections"
echo -e "  7. ${RED}Enemy Movement${NC} - Press ENTER in that terminal to start"
if [ "$DEBUG_MODE" = true ]; then
    echo -e "  8. ${MAGENTA}PX4 Debug Translator${NC} - Converting PX4 to ROS2 visualization topics"
fi
echo ""
echo -e "${CYAN}Detection Node Info:${NC}"
echo -e "  - Subscribes to: /camera/image"
echo -e "  - Publishes detections to: /enemy/detection"
echo -e "  - Publishes annotated images to: /debug/ally/detection_image"
echo -e "  - Model: YOLOv11n (will download on first run)"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo -e "  Normal mode: ./launch_multi_terminal_with_detection.sh"
echo -e "  Debug mode:  ./launch_multi_terminal_with_detection.sh --debug"
echo ""
echo -e "${GREEN}To view detection results in RViz2:${NC}"
echo -e "  1. Add an Image display"
echo -e "  2. Set the topic to /debug/ally/detection_image"
echo -e "  3. You should see bounding boxes around detected objects"
echo ""