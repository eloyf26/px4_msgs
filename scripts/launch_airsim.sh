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
    echo -e "${MAGENTA}DEBUG MODE: Enabled - Camera viewer will launch automatically${NC}"
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
pkill -f airsim_camera_bridge
pkill -f airsim_viz_translator
pkill -f rqt_image_view
pkill -f rviz2
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
echo -e "   Example: ${BLUE}cd ~/AirSimEnvironments/LinuxBlocks1.8.1/LinuxNoEditor${NC}"
echo ""
echo -e "${GREEN}2. Launch the AirSim environment${NC}"
echo -e "   Linux: ${BLUE}./Blocks.sh${NC}"
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
PX4_SYS_AUTOSTART=10016 PX4_SIM_MODEL=iris PX4_SIMULATOR=airsim ./build/px4_sitl_default/bin/px4"
open_terminal "PX4 SITL" "$PX4_CMD" "$BLUE"

# Wait for PX4 to connect to AirSim
echo -e "${YELLOW}Waiting for PX4 to connect to AirSim...${NC}"
echo -e "${YELLOW}Check PX4 terminal for 'Simulator connected on TCP port 4560'${NC}"
sleep 10

# Terminal 3: AirSim Camera Bridge (Python-based)
echo -e "${BLUE}Starting Terminal 3: AirSim Camera Bridge...${NC}"
AIRSIM_BRIDGE_CMD="echo -e '${YELLOW}=== AirSim Camera Bridge ===${NC}'; \
echo 'Starting Python-based ROS2 camera bridge...'; \
echo ''; \
echo 'Published topics:'; \
echo '  - /camera/image (sensor_msgs/Image)'; \
echo '  - /camera/camera_info (sensor_msgs/CameraInfo)'; \
echo ''; \
echo 'Configuration:'; \
echo '  - Vehicle: Ally'; \
echo '  - Camera: front_center'; \
echo '  - Rate: 30 Hz'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
echo -e '${GREEN}Camera bridge starting...${NC}'; \
ros2 run airsim_camera_bridge camera_bridge"
open_terminal "AirSim Camera Bridge" "$AIRSIM_BRIDGE_CMD" "$YELLOW"

# Wait for all nodes to initialize
sleep 3

# Terminal 4: PX4 Debug Translator (if debug mode)
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${MAGENTA}Starting Terminal 4: PX4 Debug Translator...${NC}"
    TRANSLATOR_CMD="echo -e '${MAGENTA}=== PX4 Debug Translator ===${NC}'; \
    echo 'Converting PX4 topics to ROS2 standard messages for RViz2...'; \
    echo ''; \
    echo 'Available RViz2 topics:'; \
    echo '  /debug/ally/pose (PoseStamped) - Current drone position'; \
    echo '  /debug/ally/path (Path) - Flight trajectory'; \
    echo '  /debug/ally/odometry (Odometry) - Full state estimate'; \
    echo '  /debug/ally/velocity (TwistStamped) - Current velocity'; \
    echo '  /debug/ally/setpoint (PoseStamped) - Desired position'; \
    echo '  /debug/ally/status (String) - Flight mode and arming status'; \
    echo ''; \
    source $ROS_SETUP; \
    source $WS_SETUP; \
    echo -e '${GREEN}Translator starting...${NC}'; \
    ros2 run airsim_viz_translator viz_translator"
    open_terminal "PX4 Debug Translator" "$TRANSLATOR_CMD" "$MAGENTA"
    sleep 2

    # Terminal 5: RViz2
    echo -e "${BLUE}Starting Terminal 5: RViz2 Visualization...${NC}"
    RVIZ_CMD="echo -e '${BLUE}=== RViz2 3D Visualization ===${NC}'; \
    echo 'Launching RViz2 for drone visualization...'; \
    echo ''; \
    echo 'Quick Setup:'; \
    echo '  1. Set Fixed Frame: world'; \
    echo '  2. Add → Pose → Topic: /debug/ally/pose'; \
    echo '  3. Add → Path → Topic: /debug/ally/path'; \
    echo '  4. Add → Image → Topic: /camera/image (optional)'; \
    echo ''; \
    echo 'You should see the drone position and flight path in 3D'; \
    echo ''; \
    source $ROS_SETUP; \
    source $WS_SETUP; \
    echo -e '${GREEN}Launching RViz2...${NC}'; \
    rviz2"
    open_terminal "RViz2" "$RVIZ_CMD" "$BLUE"
    sleep 2
fi

echo ""
echo -e "${GREEN}=== Core System Launched ===${NC}"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Terminal Summary                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  1. ${GREEN}MicroXRCE Agent${NC} - UDP port 8888 (PX4 ↔ ROS2 bridge)"
echo -e "  2. ${BLUE}PX4 SITL${NC} - Flight controller (connected to AirSim)"
echo -e "  3. ${YELLOW}AirSim Camera Bridge${NC} - Publishes /camera/image and /camera/camera_info"
if [ "$DEBUG_MODE" = true ]; then
    echo -e "  4. ${MAGENTA}PX4 Debug Translator${NC} - PX4 → ROS2 message conversion for RViz2"
    echo -e "  5. ${BLUE}RViz2${NC} - 3D visualization (pose, path, odometry)"
fi
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Next Steps                              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}1. Control the Ally drone:${NC}"
echo -e "   - QGroundControl should auto-connect to PX4 on UDP 14550"
echo -e "   - Or manually in PX4 terminal: ${GREEN}commander arm${NC} && ${GREEN}commander takeoff${NC}"
echo -e "   - Keyboard control in AirSim: Press ${GREEN}F1${NC} (recursive mode)"
echo ""
echo -e "${YELLOW}2. Verify camera is working:${NC}"
echo -e "   ${GREEN}ros2 topic hz /camera/image${NC}              - Check camera feed rate (~30 Hz)"
if [ "$DEBUG_MODE" = false ]; then
    echo -e "   ${GREEN}ros2 run rqt_image_view rqt_image_view${NC}   - View camera images"
fi
echo ""
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${YELLOW}3. Visualize drone in RViz2 (Terminal 5):${NC}"
    echo -e "   ${MAGENTA}RViz2 already launched automatically${NC}"
    echo -e "   - Set Fixed Frame: ${GREEN}world${NC}"
    echo -e "   - Add → Pose → Topic: ${GREEN}/debug/ally/pose${NC}"
    echo -e "   - Add → Path → Topic: ${GREEN}/debug/ally/path${NC}"
    echo -e "   - See drone position and flight trajectory in 3D"
    echo ""
fi
echo -e "${YELLOW}$(if [ "$DEBUG_MODE" = true ]; then echo "4"; else echo "3"; fi). (Optional) Launch Halcon1 detection pipeline:${NC}"
echo -e "   ${GREEN}ros2 run halcon1_detection detection_node${NC}     - YOLOv11n detection"
echo -e "   ${GREEN}ros2 run halcon1_tracking tracking_node${NC}       - Coordinate transformation"
echo -e "   ${GREEN}ros2 run halcon1_guidance guidance_node${NC}       - Kalman Filter + ProNav"
echo ""
echo -e "${YELLOW}$(if [ "$DEBUG_MODE" = true ]; then echo "5"; else echo "4"; fi). Monitor key ROS2 topics:${NC}"
echo -e "   ${GREEN}ros2 topic list${NC}                          - Show all available topics"
if [ "$DEBUG_MODE" = true ]; then
    echo -e "   ${GREEN}ros2 topic echo /debug/ally/pose${NC}         - Drone pose (RViz2 format)"
    echo -e "   ${GREEN}ros2 topic echo /debug/ally/status${NC}       - Flight mode and arming"
fi
echo -e "   ${GREEN}ros2 topic echo /fmu/out/vehicle_odometry${NC} - Drone position/velocity (PX4 format)"
echo -e "   ${GREEN}ros2 topic echo /camera/camera_info${NC}      - Camera calibration"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Troubleshooting                         ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${RED}Problem: PX4 shows 'Waiting for simulator...'${NC}"
echo -e "${YELLOW}Solution: Make sure AirSim is running and fully loaded before starting PX4${NC}"
echo ""
echo -e "${RED}Problem: No camera topics appearing${NC}"
echo -e "${YELLOW}Solution: Check AirSim Camera Bridge terminal for errors${NC}"
echo -e "${YELLOW}         Verify: ros2 topic list | grep camera${NC}"
echo -e "${YELLOW}         Check: ros2 node list | grep airsim${NC}"
echo ""
echo -e "${RED}Problem: Drone falls immediately after takeoff${NC}"
echo -e "${YELLOW}Solution: Verify LockStep is enabled in ~/Documents/AirSim/settings.json${NC}"
echo -e "${YELLOW}         Check all sensors enabled in settings.json (IMU, GPS, Barometer, Magnetometer)${NC}"
echo ""
echo -e "${GREEN}For more help, see: $REPO_ROOT/config/airsim/README.md${NC}"
echo ""
echo -e "${MAGENTA}Press Ctrl+C to stop all processes and close this launcher.${NC}"

# Wait for user to press Ctrl+C
trap "echo -e '\n${YELLOW}Stopping all processes...${NC}'; pkill -f px4; pkill -f MicroXRCEAgent; pkill -f airsim_camera_bridge; pkill -f airsim_viz_translator; pkill -f rviz2; pkill -f rqt_image_view; echo -e '${GREEN}Cleanup complete.${NC}'; exit 0" INT

# Keep script running
while true; do
    sleep 1
done
