#!/bin/bash
# Launch Halcon1 system with AirSim simulation
# This script is the AirSim equivalent of launch_multi_terminal.sh

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
AIRSIM_CONFIG="$REPO_ROOT/config/airsim/settings.json"

# ROS paths
ROS_SETUP="/opt/ros/humble/setup.bash"
WS_SETUP="$WS_ROS2/install/setup.bash"

echo -e "${GREEN}=== Halcon1 System with AirSim Launcher ===${NC}"
echo -e "${CYAN}*** AirSim + PX4 + ROS2 Integration ***${NC}"
echo -e "${YELLOW}Repository root: $REPO_ROOT${NC}"
echo -e "${YELLOW}PX4 directory: $PX4_DIR${NC}"
echo -e "${YELLOW}Workspace: $WS_ROS2${NC}"
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${MAGENTA}DEBUG MODE: Enabled${NC}"
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

if [ ! -f "$AIRSIM_CONFIG" ]; then
    echo -e "${RED}Error: AirSim config not found at $AIRSIM_CONFIG${NC}"
    echo -e "${YELLOW}Please create the config file or copy it from config/airsim/settings.json${NC}"
    exit 1
fi

# Check if AirSim config is in the correct location
AIRSIM_USER_CONFIG="$HOME/Documents/AirSim/settings.json"
if [ ! -f "$AIRSIM_USER_CONFIG" ]; then
    echo -e "${YELLOW}Warning: AirSim config not found at $AIRSIM_USER_CONFIG${NC}"
    echo -e "${YELLOW}Copying config from repository...${NC}"
    mkdir -p "$HOME/Documents/AirSim"
    cp "$AIRSIM_CONFIG" "$AIRSIM_USER_CONFIG"
    echo -e "${GREEN}Config copied successfully${NC}"
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
pkill -f airsim_node
pkill -f detection_node
pkill -f tracking_node
pkill -f guidance_node
sleep 2

# Instructions for starting AirSim
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                   IMPORTANT: Manual Step                  ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Before proceeding, you must start AirSim manually:${NC}"
echo ""
echo -e "${GREEN}1. Navigate to your AirSim environment directory${NC}"
echo -e "   Example: ${BLUE}cd ~/AirSimEnvironments/Blocks/${NC}"
echo ""
echo -e "${GREEN}2. Launch the AirSim environment${NC}"
echo -e "   Linux: ${BLUE}./LinuxBlocks.sh${NC}"
echo -e "   Windows: ${BLUE}Blocks.exe${NC}"
echo ""
echo -e "${GREEN}3. Wait for Unreal Engine to fully load${NC}"
echo -e "   You should see the AirSim HUD with 'Waiting for connection...'"
echo ""
echo -e "${YELLOW}Once AirSim is running, press ${GREEN}ENTER${YELLOW} to continue...${NC}"
read

# Terminal 1: MicroXRCE Agent
echo -e "${BLUE}Starting Terminal 1: MicroXRCE Agent...${NC}"
AGENT_CMD="echo -e '${GREEN}=== MicroXRCE Agent ===${NC}'; \
echo 'Starting agent on UDP port 8888 for PX4 communication...'; \
$MICRO_XRCE_AGENT udp4 -p 8888"
open_terminal "MicroXRCE Agent" "$AGENT_CMD" "$GREEN"

# Wait for agent to start
sleep 3

# Terminal 2: PX4 SITL (will connect to AirSim)
echo -e "${BLUE}Starting Terminal 2: PX4 SITL...${NC}"
PX4_CMD="echo -e '${GREEN}=== PX4 SITL ===${NC}'; \
echo 'Starting PX4 SITL - will connect to AirSim on TCP port 4560...'; \
echo 'LockStep mode enabled for synchronized simulation'; \
echo ''; \
cd $PX4_DIR && \
ENABLE_LOCKSTEP_SCHEDULER=yes PX4_SIM_MODEL=none ./build/px4_sitl_default/bin/px4"
open_terminal "PX4 SITL" "$PX4_CMD" "$BLUE"

# Wait for PX4 to connect to AirSim
echo -e "${YELLOW}Waiting for PX4 to connect to AirSim...${NC}"
echo -e "${YELLOW}Check PX4 terminal for 'Simulator connected on TCP port 4560'${NC}"
sleep 10

# Terminal 3: AirSim ROS Bridge (camera and other sensors)
echo -e "${BLUE}Starting Terminal 3: AirSim ROS Bridge...${NC}"
AIRSIM_BRIDGE_CMD="echo -e '${YELLOW}=== AirSim ROS Bridge ===${NC}'; \
echo 'Starting ROS2 bridge for AirSim topics...'; \
echo ''; \
echo 'Bridged topics:'; \
echo '  /airsim_node/Ally/front_center/Scene → /camera/image'; \
echo '  /airsim_node/Ally/front_center/camera_info → /camera/camera_info'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
ros2 run airsim_ros_pkgs airsim_node --ros-args \
  -p host_ip:=localhost \
  -r /airsim_node/Ally/front_center/Scene:=/camera/image \
  -r /airsim_node/Ally/front_center/camera_info:=/camera/camera_info"
open_terminal "AirSim ROS Bridge" "$AIRSIM_BRIDGE_CMD" "$YELLOW"

# Wait for bridge to start
sleep 5

# Terminal 4: Detection Node
echo -e "${CYAN}Starting Terminal 4: Detection Node (YOLOv11n)...${NC}"
DETECTION_CMD="echo -e '${CYAN}=== Detection Node (YOLOv11n) ===${NC}'; \
echo -e '${YELLOW}Starting drone detection with YOLOv11n...${NC}'; \
echo ''; \
echo 'Detection outputs:'; \
echo '  - /enemy/detection: Bounding box coordinates'; \
echo '  - /debug/ally/detection_image: Annotated camera feed'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
source $WS_ROS2/venv/bin/activate; \
echo -e '${GREEN}Detection node starting...${NC}'; \
ros2 run halcon1_detection detection_node"
open_terminal "Detection Node" "$DETECTION_CMD" "$CYAN"

# Terminal 5: Tracking Node
echo -e "${MAGENTA}Starting Terminal 5: Tracking Node...${NC}"
TRACKING_CMD="echo -e '${MAGENTA}=== Tracking Node ===${NC}'; \
echo -e '${YELLOW}Starting coordinate transformation for world tracking...${NC}'; \
echo ''; \
echo 'Tracking inputs/outputs:'; \
echo '  - Subscribes to: /enemy/detection (from Detection Node)'; \
echo '  - Subscribes to: /fmu/out/vehicle_odometry (friendly drone pose)'; \
echo '  - Publishes to: /enemy/pose (world coordinates)'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
echo -e '${GREEN}Tracking node starting...${NC}'; \
ros2 run halcon1_tracking tracking_node"
open_terminal "Tracking Node" "$TRACKING_CMD" "$MAGENTA"

# Terminal 6: Guidance Node
echo -e "${GREEN}Starting Terminal 6: Guidance Node...${NC}"
GUIDANCE_CMD="echo -e '${GREEN}=== Guidance Node ===${NC}'; \
echo -e '${YELLOW}Starting Kalman Filter + Proportional Navigation...${NC}'; \
echo ''; \
echo 'Guidance inputs/outputs:'; \
echo '  - Subscribes to: /enemy/pose (from Tracking Node)'; \
echo '  - Subscribes to: /fmu/out/vehicle_odometry (friendly drone pose)'; \
echo '  - Publishes to: /fmu/in/trajectory_setpoint (PX4 commands)'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
echo -e '${GREEN}Guidance node starting...${NC}'; \
ros2 run halcon1_guidance guidance_node"
open_terminal "Guidance Node" "$GUIDANCE_CMD" "$GREEN"

# Wait for all nodes to initialize
sleep 3

echo ""
echo -e "${GREEN}=== All nodes launched ===${NC}"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Terminal Summary                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  1. ${GREEN}MicroXRCE Agent${NC} - UDP port 8888 (PX4 ↔ ROS2 bridge)"
echo -e "  2. ${BLUE}PX4 SITL${NC} - Flight controller (connected to AirSim)"
echo -e "  3. ${YELLOW}AirSim ROS Bridge${NC} - Camera and sensor topics"
echo -e "  4. ${CYAN}Detection Node${NC} - YOLOv11n drone detection"
echo -e "  5. ${MAGENTA}Tracking Node${NC} - Coordinate transformation"
echo -e "  6. ${GREEN}Guidance Node${NC} - Kalman Filter + ProNav interception"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Next Steps                              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}1. Use QGroundControl to control the Ally drone:${NC}"
echo -e "   - QGroundControl should auto-connect to PX4 on UDP 14550"
echo -e "   - Or manually: commander arm && commander takeoff in PX4 terminal"
echo ""
echo -e "${YELLOW}2. Control the Enemy drone (optional):${NC}"
echo -e "   - Press F1 in AirSim to enable keyboard control"
echo -e "   - Or use Python API: airsim.MultirotorClient()"
echo ""
echo -e "${YELLOW}3. Monitor ROS2 topics:${NC}"
echo -e "   ${GREEN}ros2 topic hz /camera/image${NC}         - Camera feed"
echo -e "   ${GREEN}ros2 topic echo /enemy/detection${NC}    - YOLO detections"
echo -e "   ${GREEN}ros2 topic echo /enemy/pose${NC}         - Enemy world coordinates"
echo -e "   ${GREEN}ros2 topic echo /fmu/in/trajectory_setpoint${NC} - Guidance commands"
echo ""
echo -e "${YELLOW}4. Visualize with RViz2 or rqt_image_view:${NC}"
echo -e "   ${GREEN}ros2 run rqt_image_view rqt_image_view${NC}  - View camera feed"
echo -e "   ${GREEN}ros2 run rviz2 rviz2${NC}                    - 3D visualization"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Troubleshooting                         ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${RED}Problem: PX4 shows 'Waiting for simulator...'${NC}"
echo -e "${YELLOW}Solution: Make sure AirSim is running and fully loaded before starting PX4${NC}"
echo ""
echo -e "${RED}Problem: No camera topics appearing${NC}"
echo -e "${YELLOW}Solution: Check that AirSim ROS Bridge terminal shows successful connection${NC}"
echo -e "${YELLOW}         Run: ros2 topic list | grep camera${NC}"
echo ""
echo -e "${RED}Problem: Drone falls immediately after takeoff${NC}"
echo -e "${YELLOW}Solution: Verify LockStep is enabled in ~/Documents/AirSim/settings.json${NC}"
echo ""
echo -e "${GREEN}For more help, see: $REPO_ROOT/config/airsim/README.md${NC}"
echo ""
echo -e "${MAGENTA}Press Ctrl+C to stop all processes and close this launcher.${NC}"

# Wait for user to press Ctrl+C
trap "echo -e '\n${YELLOW}Stopping all processes...${NC}'; pkill -f px4; pkill -f MicroXRCEAgent; pkill -f airsim_node; pkill -f detection_node; pkill -f tracking_node; pkill -f guidance_node; echo -e '${GREEN}Cleanup complete.${NC}'; exit 0" INT

# Keep script running
while true; do
    sleep 1
done
