#!/bin/bash
# Unified launcher for Halcon1 multi-drone simulation
# Supports both Gazebo and AirSim simulators

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SIMULATOR="gazebo"
DEBUG_MODE=false

# Parse command line arguments
show_help() {
    echo -e "${GREEN}Halcon1 Multi-Drone Simulation Launcher${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --simulator <gazebo|airsim>  Choose simulator (default: gazebo)"
    echo "  --debug                      Enable RViz2 visualization and debug topics"
    echo "  --help                       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Launch Gazebo (default)"
    echo "  $0 --simulator gazebo        # Launch Gazebo explicitly"
    echo "  $0 --simulator airsim        # Launch AirSim"
    echo "  $0 --debug                   # Launch Gazebo with RViz2"
    echo "  $0 --simulator airsim --debug # Launch AirSim with RViz2"
    echo ""
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --simulator)
            SIMULATOR="$2"
            if [[ "$SIMULATOR" != "gazebo" && "$SIMULATOR" != "airsim" ]]; then
                echo -e "${RED}Error: Invalid simulator '$SIMULATOR'. Must be 'gazebo' or 'airsim'${NC}"
                exit 1
            fi
            shift 2
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo -e "${RED}Error: Unknown option '$1'${NC}"
            show_help
            ;;
    esac
done

# Get the repository root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set common paths
PX4_DIR="$REPO_ROOT/external/PX4-Autopilot"
MICRO_XRCE_AGENT="$REPO_ROOT/external/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent"
WS_ROS2="$REPO_ROOT/ws_ros2"

# ROS paths
ROS_SETUP="/opt/ros/humble/setup.bash"
WS_SETUP="$WS_ROS2/install/setup.bash"

# Print header
echo -e "${GREEN}=== Halcon1 Multi-Drone Simulation Launcher ===${NC}"
echo -e "${CYAN}*** Simulator: ${SIMULATOR^^} ***${NC}"
echo -e "${YELLOW}Repository root: $REPO_ROOT${NC}"
echo -e "${YELLOW}PX4 directory: $PX4_DIR${NC}"
echo -e "${YELLOW}Workspace: $WS_ROS2${NC}"
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${MAGENTA}DEBUG MODE: Enabled - RViz2 will launch automatically${NC}"
fi

# Check common requirements
if [ ! -d "$PX4_DIR" ]; then
    echo -e "${RED}Error: PX4 directory not found at $PX4_DIR${NC}"
    exit 1
fi

if [ ! -f "$MICRO_XRCE_AGENT" ]; then
    echo -e "${RED}Error: MicroXRCEAgent not found at $MICRO_XRCE_AGENT${NC}"
    exit 1
fi

# Simulator-specific configuration
if [ "$SIMULATOR" = "gazebo" ]; then
    # ===== GAZEBO CONFIGURATION =====
    GZ_WORLD="default"
    PX4_AUTOSTART="4001"
    PX4_GZ_SIM_RENDER_ENGINE="ogre2"
    export LIBGL_ALWAYS_SOFTWARE=1

    # Ally drone configuration
    ALLY_INSTANCE=0
    ALLY_X=0
    ALLY_Y=0
    ALLY_Z=0
    ALLY_ROLL=0
    ALLY_PITCH=0
    ALLY_YAW=0
    ALLY_MODEL="x500_mono_cam"
    ALLY_POSITION="${ALLY_X},${ALLY_Y},${ALLY_Z},${ALLY_ROLL},${ALLY_PITCH},${ALLY_YAW}"

    # Enemy drone configuration
    ENEMY_INSTANCE=$((ALLY_INSTANCE + 1))
    ENEMY_X=5
    ENEMY_Y=0
    ENEMY_Z=0
    ENEMY_ROLL=0
    ENEMY_PITCH=0
    ENEMY_YAW=0
    ENEMY_POSITION="${ENEMY_X},${ENEMY_Y},${ENEMY_Z},${ENEMY_ROLL},${ENEMY_PITCH},${ENEMY_YAW}"

    # Camera configuration
    GAZEBO_MODEL_NAME="${ALLY_MODEL}_${ALLY_INSTANCE}"

elif [ "$SIMULATOR" = "airsim" ]; then
    # ===== AIRSIM CONFIGURATION =====
    AIRSIM_CONFIG="$REPO_ROOT/config/airsim/settings.json"
    AIRSIM_USER_CONFIG="$HOME/Documents/AirSim/settings.json"

    # Check if AirSim config exists
    if [ ! -f "$AIRSIM_CONFIG" ]; then
        echo -e "${RED}Error: AirSim config not found at $AIRSIM_CONFIG${NC}"
        exit 1
    fi

    # Check if AirSim config is in the correct location
    if [ ! -f "$AIRSIM_USER_CONFIG" ]; then
        echo -e "${YELLOW}Warning: AirSim config not found at $AIRSIM_USER_CONFIG${NC}"
        echo -e "${YELLOW}Copying config from repository...${NC}"
        mkdir -p "$HOME/Documents/AirSim"
        cp "$AIRSIM_CONFIG" "$AIRSIM_USER_CONFIG"
        echo -e "${GREEN}Config copied successfully${NC}"
    fi

    # Auto-detect AirSim environment
    AIRSIM_ENV_DIR=""
    AIRSIM_LAUNCH_SCRIPT=""

    # Check common locations
    if [ -f "$HOME/AirSimEnvironments/LinuxBlocks1.8.1/LinuxNoEditor/Blocks.sh" ]; then
        AIRSIM_ENV_DIR="$HOME/AirSimEnvironments/LinuxBlocks1.8.1/LinuxNoEditor"
        AIRSIM_LAUNCH_SCRIPT="Blocks.sh"
    elif [ -f "$HOME/AirSimEnvironments/Blocks/LinuxNoEditor/Blocks.sh" ]; then
        AIRSIM_ENV_DIR="$HOME/AirSimEnvironments/Blocks/LinuxNoEditor"
        AIRSIM_LAUNCH_SCRIPT="Blocks.sh"
    elif [ -f "$HOME/AirSimEnvironments/LandscapeMountains/LinuxNoEditor/LandscapeMountains.sh" ]; then
        AIRSIM_ENV_DIR="$HOME/AirSimEnvironments/LandscapeMountains/LinuxNoEditor"
        AIRSIM_LAUNCH_SCRIPT="LandscapeMountains.sh"
    elif [ -f "$HOME/AirSimEnvironments/CityEnviron/LinuxNoEditor/CityEnviron.sh" ]; then
        AIRSIM_ENV_DIR="$HOME/AirSimEnvironments/CityEnviron/LinuxNoEditor"
        AIRSIM_LAUNCH_SCRIPT="CityEnviron.sh"
    fi

    if [ -z "$AIRSIM_ENV_DIR" ]; then
        echo -e "${RED}Error: AirSim environment not found in common locations${NC}"
        echo -e "${YELLOW}Please install an AirSim environment using:${NC}"
        echo -e "  ${GREEN}./scripts/install_airsim_env.sh --blocks${NC}"
        echo ""
        echo -e "${YELLOW}Or manually specify the path by setting AIRSIM_ENV_DIR:${NC}"
        echo -e "  ${GREEN}export AIRSIM_ENV_DIR=/path/to/AirSimEnvironment/LinuxNoEditor${NC}"
        echo -e "  ${GREEN}export AIRSIM_LAUNCH_SCRIPT=Blocks.sh${NC}"
        echo -e "  ${GREEN}$0 --simulator airsim${NC}"
        exit 1
    fi

    echo -e "${GREEN}Found AirSim environment: $AIRSIM_ENV_DIR/$AIRSIM_LAUNCH_SCRIPT${NC}"
fi

# Terminal counter for positioning
TERMINAL_NUM=0

# Function to open a new terminal with a command
open_terminal() {
    local title="$1"
    local command="$2"
    local color="$3"

    # Calculate grid position (3 columns)
    local cols=3
    local term_width=640
    local term_height=400
    local row=$((TERMINAL_NUM / cols))
    local col=$((TERMINAL_NUM % cols))
    local x=$((col * term_width))
    local y=$((row * term_height))

    TERMINAL_NUM=$((TERMINAL_NUM + 1))

    # Try different terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$title" --geometry=100x24+$x+$y -- bash -c "$command; echo -e '${color}[Process exited. Press Enter to close]${NC}'; read" &
        sleep 0.3  # Small delay to ensure proper window positioning
    elif command -v xterm &> /dev/null; then
        xterm -title "$title" -geometry 100x24+$x+$y -e bash -c "$command; echo -e '${color}[Process exited. Press Enter to close]${NC}'; read" &
        sleep 0.3
    elif command -v konsole &> /dev/null; then
        konsole --new-tab --title "$title" -e bash -c "$command; echo -e '${color}[Process exited. Press Enter to close]${NC}'; read" &
        sleep 0.3
    elif command -v terminator &> /dev/null; then
        terminator --new-window --title="$title" --geometry=100x24+$x+$y -e bash -c "$command; echo -e '${color}[Process exited. Press Enter to close]${NC}'; read" &
        sleep 0.3
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
pkill -f airsim_camera_bridge
pkill -f airsim_viz_translator
pkill -f detection_node
pkill -f tracking_node
pkill -f guidance_node
pkill -f rqt_image_view
pkill -f rviz2
# Kill AirSim/Unreal processes
pkill -f Blocks
pkill -f LandscapeMountains
pkill -f CityEnviron
pkill -f "UE4\|UnrealEngine"
sleep 2

# AirSim-specific startup - Launch AirSim environment automatically
if [ "$SIMULATOR" = "airsim" ]; then
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           Launching AirSim Environment                    ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Starting AirSim environment: $AIRSIM_LAUNCH_SCRIPT${NC}"
    echo -e "${YELLOW}Please wait for Unreal Engine to fully load...${NC}"
    echo ""

    # Launch AirSim in a separate terminal (Terminal 0 - before the main terminals)
    AIRSIM_CMD="echo -e '${BLUE}=== AirSim Environment ===${NC}'; \
    echo 'Starting Unreal Engine environment...'; \
    echo 'Location: $AIRSIM_ENV_DIR'; \
    echo 'Script: $AIRSIM_LAUNCH_SCRIPT'; \
    echo ''; \
    echo 'Wait for the environment to fully load before launching other components'; \
    echo 'You should see the AirSim HUD with vehicle information'; \
    echo ''; \
    cd $AIRSIM_ENV_DIR && bash $AIRSIM_LAUNCH_SCRIPT"
    open_terminal "AirSim Environment" "$AIRSIM_CMD" "$BLUE"

    echo -e "${YELLOW}Waiting 20 seconds for AirSim/Unreal Engine to initialize...${NC}"
    sleep 20
fi

# Terminal 1: MicroXRCE Agent
echo -e "${BLUE}Starting Terminal 1: MicroXRCE Agent...${NC}"
AGENT_CMD="echo -e '${GREEN}=== MicroXRCE Agent ===${NC}'; \
echo 'Starting agent on UDP port 8888 for PX4 communication...'; \
$MICRO_XRCE_AGENT udp4 -p 8888"
open_terminal "MicroXRCE Agent" "$AGENT_CMD" "$GREEN"
sleep 3

# Terminal 2: PX4 SITL - Ally
echo -e "${BLUE}Starting Terminal 2: PX4 SITL - Ally...${NC}"
if [ "$SIMULATOR" = "gazebo" ]; then
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
    echo -e "${YELLOW}Waiting for Gazebo to initialize...${NC}"
    sleep 15
else
    # AirSim
    ALLY_CMD="echo -e '${GREEN}=== PX4 SITL ===${NC}'; \
echo 'Starting PX4 SITL - will connect to AirSim on TCP port 4560...'; \
echo 'LockStep mode enabled for synchronized simulation'; \
echo ''; \
cd $PX4_DIR && \
PX4_SYS_AUTOSTART=10016 PX4_SIM_MODEL=iris PX4_SIMULATOR=airsim ./build/px4_sitl_default/bin/px4"
    open_terminal "PX4 SITL" "$ALLY_CMD" "$BLUE"
    echo -e "${YELLOW}Waiting for PX4 to connect to AirSim...${NC}"
    echo -e "${YELLOW}Check PX4 terminal for 'Simulator connected on TCP port 4560'${NC}"
    sleep 10
fi

# Terminal 3: Camera Bridge (simulator-specific)
echo -e "${BLUE}Starting Terminal 3: Camera Bridge...${NC}"
if [ "$SIMULATOR" = "gazebo" ]; then
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
else
    # AirSim
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
fi
sleep 3

# Terminal 4: Detection Node
echo -e "${CYAN}Starting Terminal 4: Detection Node...${NC}"
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
echo -e "${CYAN}Starting Terminal 5: Tracking Node...${NC}"
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
echo -e "${CYAN}Starting Terminal 6: Guidance Node...${NC}"
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

# Terminal 7: Enemy Drone Control (simulator-specific)
echo -e "${MAGENTA}Starting Terminal 7: Enemy Drone Controller...${NC}"
if [ "$SIMULATOR" = "gazebo" ]; then
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
    sleep 5

    # Launch enemy movement control
    echo -e "${BLUE}Starting Terminal 8: Enemy Movement Control...${NC}"
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
else
    # AirSim
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
fi
sleep 2

# Terminal 8/9: PX4 Debug Translator (if debug mode)
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${MAGENTA}Starting Terminal 8: PX4 Debug Translator...${NC}"

    if [ "$SIMULATOR" = "gazebo" ]; then
        # Gazebo debug translator
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
ros2 run multi_drone_sim px4_debug_translator \
--ros-args \
-p enemy_offset_x:=${ENEMY_X}.0 \
-p enemy_offset_y:=${ENEMY_Y}.0 \
-p enemy_offset_z:=${ENEMY_Z}.0"
        open_terminal "PX4 Debug Translator" "$DEBUG_CMD" "$MAGENTA"
    else
        # AirSim debug translator
        AIRSIM_SETTINGS="$HOME/Documents/AirSim/settings.json"
        if [ -f "$AIRSIM_SETTINGS" ]; then
            # Extract Ally spawn coordinates
            ALLY_X=$(grep -A 20 '"Ally"' "$AIRSIM_SETTINGS" | grep '"X"' | head -1 | sed 's/.*: *\([0-9.-]*\).*/\1/')
            ALLY_Y=$(grep -A 20 '"Ally"' "$AIRSIM_SETTINGS" | grep '"Y"' | head -1 | sed 's/.*: *\([0-9.-]*\).*/\1/')
            ALLY_Z=$(grep -A 20 '"Ally"' "$AIRSIM_SETTINGS" | grep '"Z"' | head -1 | sed 's/.*: *\([0-9.-]*\).*/\1/')

            # Default to 0.0 if extraction failed
            ALLY_X=${ALLY_X:-0.0}
            ALLY_Y=${ALLY_Y:-0.0}
            ALLY_Z=${ALLY_Z:-0.0}

            # Ensure float format
            [[ ! "$ALLY_X" =~ \. ]] && ALLY_X="${ALLY_X}.0"
            [[ ! "$ALLY_Y" =~ \. ]] && ALLY_Y="${ALLY_Y}.0"
            [[ ! "$ALLY_Z" =~ \. ]] && ALLY_Z="${ALLY_Z}.0"

            echo -e "${CYAN}Ally spawn position from settings.json: X=$ALLY_X, Y=$ALLY_Y, Z=$ALLY_Z${NC}"
        else
            echo -e "${YELLOW}Warning: AirSim settings.json not found, using default Ally spawn (0,0,0)${NC}"
            ALLY_X=0.0
            ALLY_Y=0.0
            ALLY_Z=0.0
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
echo '  Enemy Drone:'; \
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
    fi
    sleep 2

    # Terminal 9/10: RViz2
    echo -e "${BLUE}Starting Terminal 9: RViz2 Visualization...${NC}"
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

# Print summary
echo ""
echo -e "${GREEN}=== System Launched ===${NC}"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Terminal Summary                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$SIMULATOR" = "airsim" ]; then
    echo -e "  0. ${BLUE}AirSim Environment${NC} - Unreal Engine simulation"
fi

echo -e "  1. ${GREEN}MicroXRCE Agent${NC} - UDP port 8888 (PX4 ↔ ROS2 bridge)"
echo -e "  2. ${BLUE}PX4 SITL - Ally${NC} - Flight controller"
echo -e "  3. ${YELLOW}Camera Bridge${NC} - Publishes /camera/image and /camera/camera_info"
echo -e "  4. ${CYAN}Detection Node${NC} - YOLOv11n drone detection"
echo -e "  5. ${CYAN}Tracking Node${NC} - Camera-to-world coordinate transform"
echo -e "  6. ${CYAN}Guidance Node${NC} - Kalman Filter + Proportional Navigation"

if [ "$SIMULATOR" = "gazebo" ]; then
    echo -e "  7. ${RED}Enemy Drone${NC} - PX4 SITL Instance $ENEMY_INSTANCE"
    echo -e "  8. ${RED}Enemy Movement Control${NC} - Offboard control (interactive)"
    TERM_NUM=8
else
    echo -e "  7. ${MAGENTA}Enemy Drone Controller${NC} - SimpleFlight API control (interactive)"
    TERM_NUM=7
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

if [ "$SIMULATOR" = "gazebo" ]; then
    echo -e "${YELLOW}1. Control the Ally drone:${NC}"
    echo -e "   - QGroundControl should auto-connect to PX4 on UDP 14550"
    echo -e "   - Or manually in PX4 terminal: ${GREEN}commander arm${NC} && ${GREEN}commander takeoff${NC}"
    echo ""
    echo -e "${YELLOW}2. Control the Enemy drone:${NC}"
    echo -e "   - In Enemy Movement Control terminal, press ENTER to start"
    echo -e "   - ${RED}IMPORTANT:${NC} Arm/takeoff Ally first, then start Enemy"
    echo ""
    echo -e "${YELLOW}3. Verify camera is working:${NC}"
    echo -e "   ${GREEN}ros2 topic hz /camera/image${NC}              - Check camera feed rate (~30 Hz)"
    if [ "$DEBUG_MODE" = false ]; then
        echo -e "   ${GREEN}ros2 run rqt_image_view rqt_image_view${NC}   - View camera images"
    fi
else
    echo -e "${YELLOW}1. Control the Ally drone (PX4Multirotor):${NC}"
    echo -e "   - QGroundControl should auto-connect to PX4 on UDP 14550"
    echo -e "   - Or manually in PX4 terminal: ${GREEN}commander arm${NC} && ${GREEN}commander takeoff${NC}"
    echo ""
    echo -e "${YELLOW}2. Control the Enemy drone (SimpleFlight):${NC}"
    echo -e "   - In Enemy Drone Controller terminal, press ENTER to start"
    echo -e "   - Select movement pattern: 1=Circular, 2=Figure-8, 3=Random, 4=Hover"
    echo -e "   - ${RED}IMPORTANT:${NC} Arm/takeoff Ally first, then start Enemy"
    echo ""
    echo -e "${YELLOW}3. Verify camera is working:${NC}"
    echo -e "   ${GREEN}ros2 topic hz /camera/image${NC}              - Check camera feed rate (~30 Hz)"
    if [ "$DEBUG_MODE" = false ]; then
        echo -e "   ${GREEN}ros2 run rqt_image_view rqt_image_view${NC}   - View camera images"
    fi
fi

echo ""
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${YELLOW}4. Visualize drone in RViz2:${NC}"
    echo -e "   ${MAGENTA}RViz2 already launched automatically${NC}"
    echo -e "   - Set Fixed Frame: ${GREEN}world${NC}"
    echo -e "   - Add → Pose → Topic: ${GREEN}/debug/ally/pose${NC}"
    echo -e "   - Add → Path → Topic: ${GREEN}/debug/ally/path${NC}"
    echo -e "   - See drone position and flight trajectory in 3D"
    echo ""
    NEXT_STEP=5
else
    NEXT_STEP=4
fi

echo -e "${GREEN}$NEXT_STEP. Halcon1 pipeline is running automatically!${NC}"
echo -e "   ${CYAN}Detection, Tracking, and Guidance nodes are already active${NC}"
echo -e "   ${CYAN}Check terminals 4, 5, 6 for node status${NC}"
echo ""
NEXT_STEP=$((NEXT_STEP + 1))
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

if [ "$SIMULATOR" = "gazebo" ]; then
    echo -e "${RED}Problem: Gazebo doesn't start or crashes${NC}"
    echo -e "${YELLOW}Solution: Check Gazebo terminal for errors, ensure graphics drivers installed${NC}"
    echo ""
    echo -e "${RED}Problem: Camera topics not appearing${NC}"
    echo -e "${YELLOW}Solution: Check Camera Bridge terminal for errors${NC}"
    echo -e "${YELLOW}         Verify: ros2 topic list | grep camera${NC}"
else
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
fi

echo ""
echo -e "${GREEN}For more help:${NC}"
if [ "$SIMULATOR" = "gazebo" ]; then
    echo -e "  - Gazebo docs: $REPO_ROOT/README.md"
else
    echo -e "  - AirSim docs: $REPO_ROOT/config/airsim/README.md"
    echo -e "  - Multi-drone: $REPO_ROOT/docs/MULTI_DRONE_AIRSIM.md"
fi
echo -e "  - Cleanup: ${GREEN}./scripts/cleanup.sh${NC}"
echo ""
echo -e "${MAGENTA}Press Ctrl+C to stop all processes and close this launcher.${NC}"

# Wait for user to press Ctrl+C
trap "echo -e '\n${YELLOW}Stopping all processes...${NC}'; $SCRIPT_DIR/cleanup.sh; exit 0" INT

# Keep script running
while true; do
    sleep 1
done
