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
MULTI_DRONE=false
for arg in "$@"; do
    case $arg in
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --multi)
            MULTI_DRONE=true
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
    echo -e "${MAGENTA}DEBUG MODE: Enabled - RViz2 will launch automatically${NC}"
fi
if [ "$MULTI_DRONE" = true ]; then
    echo -e "${MAGENTA}MULTI-DRONE MODE: Enabled - Enemy drone control will launch${NC}"
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

# Halcon1 Pipeline Nodes (Detection, Tracking, Guidance)
TERMINAL_COUNT=3

# Terminal 4: Detection Node
TERMINAL_COUNT=$((TERMINAL_COUNT + 1))
echo -e "${CYAN}Starting Terminal $TERMINAL_COUNT: Detection Node...${NC}"

# Build detection command based on debug mode
if [ "$DEBUG_MODE" = true ]; then
    DEBUG_TOPICS="echo '  - /debug/ally/detection_image (sensor_msgs/Image)'; \
echo '';"
    DETECTION_CMD="echo -e '${CYAN}=== Halcon1 Detection Node ===${NC}'; \
echo 'YOLOv11n drone detection'; \
echo ''; \
echo 'Subscribed topics:'; \
echo '  - /camera/image (sensor_msgs/Image)'; \
echo ''; \
echo 'Published topics:'; \
echo '  - /enemy/detection (halcon1_msgs/Detection)'; \
$DEBUG_TOPICS \
echo 'Loading YOLO model...'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
if [ -d '$WS_ROS2/venv' ]; then \
    source $WS_ROS2/venv/bin/activate; \
fi; \
echo -e '${GREEN}Detection node starting...${NC}'; \
ros2 run halcon1_detection detection_node --ros-args -p debug:=true"
else
    DETECTION_CMD="echo -e '${CYAN}=== Halcon1 Detection Node ===${NC}'; \
echo 'YOLOv11n drone detection'; \
echo ''; \
echo 'Subscribed topics:'; \
echo '  - /camera/image (sensor_msgs/Image)'; \
echo ''; \
echo 'Published topics:'; \
echo '  - /enemy/detection (halcon1_msgs/Detection)'; \
echo ''; \
echo 'Loading YOLO model...'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
if [ -d '$WS_ROS2/venv' ]; then \
    source $WS_ROS2/venv/bin/activate; \
fi; \
echo -e '${GREEN}Detection node starting...${NC}'; \
ros2 run halcon1_detection detection_node"
fi
open_terminal "Detection Node" "$DETECTION_CMD" "$CYAN"
sleep 2

# Terminal 5: Tracking Node
TERMINAL_COUNT=$((TERMINAL_COUNT + 1))
echo -e "${CYAN}Starting Terminal $TERMINAL_COUNT: Tracking Node...${NC}"
TRACKING_CMD="echo -e '${CYAN}=== Halcon1 Tracking Node ===${NC}'; \
echo 'Camera-to-world coordinate transformation'; \
echo ''; \
echo 'Subscribed topics:'; \
echo '  - /enemy/detection (halcon1_msgs/Detection)'; \
echo '  - /camera/camera_info (sensor_msgs/CameraInfo)'; \
echo '  - /fmu/out/vehicle_odometry (px4_msgs/VehicleOdometry)'; \
echo ''; \
echo 'Published topics:'; \
echo '  - /enemy/pose (geometry_msgs/PoseStamped)'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
echo -e '${GREEN}Tracking node starting...${NC}'; \
ros2 run halcon1_tracking tracking_node"
open_terminal "Tracking Node" "$TRACKING_CMD" "$CYAN"
sleep 2

# Terminal 6: Guidance Node
TERMINAL_COUNT=$((TERMINAL_COUNT + 1))
echo -e "${CYAN}Starting Terminal $TERMINAL_COUNT: Guidance Node...${NC}"
GUIDANCE_CMD="echo -e '${CYAN}=== Halcon1 Guidance Node ===${NC}'; \
echo 'Kalman Filter + Proportional Navigation'; \
echo ''; \
echo 'Subscribed topics:'; \
echo '  - /enemy/tracked (halcon1_msgs/TrackedObject)'; \
echo '  - /fmu/out/vehicle_odometry (px4_msgs/VehicleOdometry)'; \
echo ''; \
echo 'Published topics:'; \
echo '  - /interception/command (halcon1_msgs/InterceptionCommand)'; \
echo '  - /fmu/in/trajectory_setpoint (px4_msgs/TrajectorySetpoint)'; \
echo ''; \
source $ROS_SETUP; \
source $WS_SETUP; \
echo -e '${GREEN}Guidance node starting...${NC}'; \
ros2 run halcon1_guidance guidance_node"
open_terminal "Guidance Node" "$GUIDANCE_CMD" "$CYAN"
sleep 2

# Terminal 7: Enemy Drone Controller (if multi-drone mode)
if [ "$MULTI_DRONE" = true ]; then
    TERMINAL_COUNT=$((TERMINAL_COUNT + 1))
    echo -e "${MAGENTA}Starting Terminal $TERMINAL_COUNT: Enemy Drone Controller...${NC}"
    ENEMY_CMD="echo -e '${MAGENTA}=== Enemy Drone Controller ===${NC}'; \
    echo 'Waiting for user input to start enemy drone...'; \
    echo ''; \
    echo 'IMPORTANT: Wait for Ally drone to takeoff first!'; \
    echo ''; \
    echo 'Movement patterns available:'; \
    echo '  1. Circular    - Fly in a circle'; \
    echo '  2. Figure-8    - Fly in a figure-8 pattern'; \
    echo '  3. Random      - Move to random positions'; \
    echo '  4. Hover       - Hover at current position'; \
    echo ''; \
    echo -e '${GREEN}Press ENTER when ready to start enemy control...${NC}'; \
    read; \
    python3 $REPO_ROOT/scripts/control_enemy_airsim.py --altitude 5 --speed 3 --radius 8"
    open_terminal "Enemy Drone Controller" "$ENEMY_CMD" "$MAGENTA"
    sleep 2
fi

# Terminal 8 or 7: PX4 Debug Translator (if debug mode)
if [ "$DEBUG_MODE" = true ]; then
    TERMINAL_COUNT=$((TERMINAL_COUNT + 1))
    echo -e "${MAGENTA}Starting Terminal $TERMINAL_COUNT: PX4 Debug Translator...${NC}"

    # Read Ally spawn position from AirSim settings.json
    AIRSIM_SETTINGS="$HOME/Documents/AirSim/settings.json"
    if [ -f "$AIRSIM_SETTINGS" ]; then
        # Extract Ally spawn coordinates using grep and sed
        ALLY_X=$(grep -A 20 '"Ally"' "$AIRSIM_SETTINGS" | grep '"X"' | head -1 | sed 's/.*: *\([0-9.-]*\).*/\1/')
        ALLY_Y=$(grep -A 20 '"Ally"' "$AIRSIM_SETTINGS" | grep '"Y"' | head -1 | sed 's/.*: *\([0-9.-]*\).*/\1/')
        ALLY_Z=$(grep -A 20 '"Ally"' "$AIRSIM_SETTINGS" | grep '"Z"' | head -1 | sed 's/.*: *\([0-9.-]*\).*/\1/')

        # Default to 0 if extraction failed
        ALLY_X=${ALLY_X:-0}
        ALLY_Y=${ALLY_Y:-0}
        ALLY_Z=${ALLY_Z:-0}

        echo -e "${CYAN}Ally spawn position from settings.json: X=$ALLY_X, Y=$ALLY_Y, Z=$ALLY_Z${NC}"
    else
        echo -e "${YELLOW}Warning: AirSim settings.json not found, using default Ally spawn (0,0,0)${NC}"
        ALLY_X=0
        ALLY_Y=0
        ALLY_Z=0
    fi

    TRANSLATOR_CMD="echo -e '${MAGENTA}=== PX4 Debug Translator ===${NC}'; \
    echo 'Converting PX4 and Halcon1 topics to RViz2 standard messages...'; \
    echo ''; \
    echo 'Available RViz2 topics:'; \
    echo '  Ally Drone:'; \
    echo '    /debug/ally/pose (PoseStamped) - Current position'; \
    echo '    /debug/ally/path (Path) - Flight trajectory'; \
    echo '    /debug/ally/odometry (Odometry) - Full state'; \
    echo '    /debug/ally/velocity (TwistStamped) - Current velocity'; \
    echo '    /debug/ally/setpoint (PoseStamped) - Desired position'; \
    echo '    /debug/ally/status (String) - Flight mode'; \
    echo '  Enemy Drone (if multi-drone):'; \
    echo '    /debug/enemy/pose (PoseStamped) - Ground truth from AirSim'; \
    echo '    /debug/enemy/path (Path) - Ground truth trajectory'; \
    echo ''; \
    source $ROS_SETUP; \
    source $WS_SETUP; \
    echo -e '${GREEN}Translator starting...${NC}'; \
    ros2 run airsim_viz_translator viz_translator \
        --ros-args \
        -p ally_spawn_x:=$ALLY_X \
        -p ally_spawn_y:=$ALLY_Y \
        -p ally_spawn_z:=$ALLY_Z"
    open_terminal "PX4 Debug Translator" "$TRANSLATOR_CMD" "$MAGENTA"
    sleep 2

    # Terminal 9 or 8: RViz2
    TERMINAL_COUNT=$((TERMINAL_COUNT + 1))
    echo -e "${BLUE}Starting Terminal $TERMINAL_COUNT: RViz2 Visualization...${NC}"
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
echo -e "  4. ${CYAN}Detection Node${NC} - YOLOv11n drone detection"
echo -e "  5. ${CYAN}Tracking Node${NC} - Camera-to-world coordinate transform"
echo -e "  6. ${CYAN}Guidance Node${NC} - Kalman Filter + Proportional Navigation"

TERM_NUM=6
if [ "$MULTI_DRONE" = true ]; then
    TERM_NUM=$((TERM_NUM + 1))
    echo -e "  $TERM_NUM. ${MAGENTA}Enemy Drone Controller${NC} - SimpleFlight API control (interactive)"
fi
if [ "$DEBUG_MODE" = true ]; then
    TERM_NUM=$((TERM_NUM + 1))
    echo -e "  $TERM_NUM. ${MAGENTA}PX4 Debug Translator${NC} - PX4 → ROS2 message conversion for RViz2"
    TERM_NUM=$((TERM_NUM + 1))
    echo -e "  $TERM_NUM. ${BLUE}RViz2${NC} - 3D visualization (pose, path, odometry)"
fi
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Next Steps                              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}1. Control the Ally drone (PX4Multirotor):${NC}"
echo -e "   - QGroundControl should auto-connect to PX4 on UDP 14550"
echo -e "   - Or manually in PX4 terminal: ${GREEN}commander arm${NC} && ${GREEN}commander takeoff${NC}"
echo ""
NEXT_STEP=2
if [ "$MULTI_DRONE" = true ]; then
    echo -e "${YELLOW}2. Control the Enemy drone (SimpleFlight):${NC}"
    echo -e "   - In Enemy Drone Controller terminal, press ENTER to start"
    echo -e "   - Select movement pattern: 1=Circular, 2=Figure-8, 3=Random, 4=Hover"
    echo -e "   - ${RED}IMPORTANT:${NC} Arm/takeoff Ally first, then start Enemy"
    echo ""
    NEXT_STEP=3
fi
echo -e "${YELLOW}$NEXT_STEP. Verify camera is working:${NC}"
NEXT_STEP=$((NEXT_STEP + 1))
echo -e "   ${GREEN}ros2 topic hz /camera/image${NC}              - Check camera feed rate (~30 Hz)"
if [ "$DEBUG_MODE" = false ]; then
    echo -e "   ${GREEN}ros2 run rqt_image_view rqt_image_view${NC}   - View camera images"
fi
echo ""
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${YELLOW}$NEXT_STEP. Visualize drone in RViz2:${NC}"
    echo -e "   ${MAGENTA}RViz2 already launched automatically${NC}"
    echo -e "   - Set Fixed Frame: ${GREEN}world${NC}"
    echo -e "   - Add → Pose → Topic: ${GREEN}/debug/ally/pose${NC}"
    echo -e "   - Add → Path → Topic: ${GREEN}/debug/ally/path${NC}"
    echo -e "   - See drone position and flight trajectory in 3D"
    echo ""
    NEXT_STEP=$((NEXT_STEP + 1))
fi
echo -e "${GREEN}$NEXT_STEP. Halcon1 pipeline is running automatically!${NC}"
NEXT_STEP=$((NEXT_STEP + 1))
echo -e "   ${CYAN}Detection, Tracking, and Guidance nodes are already active${NC}"
echo -e "   ${CYAN}Check terminals 4, 5, 6 for node status${NC}"
echo ""
echo -e "${YELLOW}$NEXT_STEP. Monitor pipeline topics:${NC}"
echo -e "   ${GREEN}ros2 topic echo /enemy/detection --once${NC}      - Detection results"
echo -e "   ${GREEN}ros2 topic echo /enemy/tracked --once${NC}        - 3D world coordinates"
echo -e "   ${GREEN}ros2 topic echo /interception/command --once${NC} - Guidance commands"
echo -e "   ${GREEN}ros2 topic hz /camera/image${NC}                  - Camera rate (~30 Hz)"
if [ "$DEBUG_MODE" = true ]; then
    echo -e "   ${GREEN}ros2 topic echo /debug/ally/pose --once${NC}      - Drone pose (RViz2)"
fi
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
