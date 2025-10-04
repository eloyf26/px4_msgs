#!/bin/bash
# Unified cleanup script for Halcon1 simulation
# Works for both Gazebo and AirSim simulators

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Halcon1 Simulation Cleanup ===${NC}"
echo -e "${CYAN}Cleaning up processes from both Gazebo and AirSim...${NC}"

# Function to kill processes safely
kill_process() {
    local process_name="$1"
    local pids=$(pgrep -f "$process_name")

    if [ ! -z "$pids" ]; then
        echo -e "${RED}Killing $process_name processes: $pids${NC}"
        for pid in $pids; do
            kill -TERM $pid 2>/dev/null
        done
        sleep 1
        # Force kill if still running
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}Force killing PID $pid${NC}"
                kill -KILL $pid 2>/dev/null
            fi
        done
    else
        echo -e "${GREEN}No $process_name processes found${NC}"
    fi
}

# Kill PX4 instances
echo -e "${YELLOW}Stopping PX4 instances...${NC}"
kill_process "px4"

# Kill MicroXRCE Agent
echo -e "${YELLOW}Stopping MicroXRCE Agent...${NC}"
kill_process "MicroXRCEAgent"

# Kill Gazebo processes
echo -e "${YELLOW}Stopping Gazebo...${NC}"
kill_process "gz sim"
kill_process "gz gui"
kill_process "gzserver"
kill_process "gzclient"
kill_process "ruby.*gz"
kill_process "ign gazebo"
kill_process "ignition"
pkill -f "gazebo" 2>/dev/null
pkill -f "gz" 2>/dev/null

# Kill AirSim/Unreal processes
echo -e "${YELLOW}Stopping AirSim/Unreal processes...${NC}"
kill_process "Blocks"
kill_process "CityEnviron"
kill_process "LandscapeMountains"
kill_process "AirSim"
kill_process "UE4"
kill_process "UnrealEngine"

# Kill ROS2 nodes
echo -e "${YELLOW}Stopping ROS2 nodes...${NC}"
# Gazebo-specific nodes
kill_process "ros2.*parameter_bridge"
kill_process "ros_gz_bridge"
kill_process "enemy_offboard_control"
kill_process "px4_debug_translator"

# AirSim-specific nodes
kill_process "airsim_camera_bridge"
kill_process "airsim_viz_translator"
kill_process "control_enemy_airsim"

# Halcon1 pipeline nodes
kill_process "detection_node"
kill_process "tracking_node"
kill_process "guidance_node"

# Visualization tools
kill_process "rqt_image_view"
kill_process "rviz2"

# Kill terminal emulators spawned by scripts
echo -e "${YELLOW}Stopping terminal emulators spawned by script...${NC}"
kill_process "gnome-terminal.*MicroXRCE Agent"
kill_process "gnome-terminal.*PX4 SITL"
kill_process "gnome-terminal.*Ally Drone"
kill_process "gnome-terminal.*Enemy Drone"
kill_process "gnome-terminal.*Camera Bridge"
kill_process "gnome-terminal.*AirSim Camera Bridge"
kill_process "gnome-terminal.*Detection Node"
kill_process "gnome-terminal.*Tracking Node"
kill_process "gnome-terminal.*Guidance Node"
kill_process "gnome-terminal.*Enemy Movement"
kill_process "gnome-terminal.*Enemy Drone Controller"
kill_process "gnome-terminal.*PX4 Debug Translator"
kill_process "gnome-terminal.*RViz2"
kill_process "gnome-terminal.*Camera Viewer"

# Clean up temporary files
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -f /tmp/.X*lock 2>/dev/null
# Gazebo temp files
rm -rf /tmp/gz* 2>/dev/null
# AirSim temp files
rm -rf /tmp/AirSim* 2>/dev/null
# Test detection images
rm -f /tmp/test_input.jpg 2>/dev/null
rm -f /tmp/test_annotated.jpg 2>/dev/null

# Check for remaining processes
echo -e "${GREEN}Checking for remaining processes...${NC}"
remaining_px4=$(pgrep -c px4)
remaining_gz=$(pgrep -c -f "gz\|gazebo\|ignition")
remaining_airsim=$(pgrep -c -f "Blocks\|CityEnviron\|LandscapeMountains\|AirSim\|UE4\|UnrealEngine")
remaining_agent=$(pgrep -c MicroXRCEAgent)
remaining_camera_gz=$(pgrep -c -f "ros_gz_bridge\|ros2.*parameter_bridge")
remaining_camera_airsim=$(pgrep -c airsim_camera_bridge)
remaining_viz=$(pgrep -c -f "airsim_viz_translator\|px4_debug_translator")
remaining_detection=$(pgrep -c detection_node)
remaining_tracking=$(pgrep -c tracking_node)
remaining_guidance=$(pgrep -c guidance_node)
remaining_rviz=$(pgrep -c rviz2)

# Calculate total remaining
total_remaining=$((remaining_px4 + remaining_gz + remaining_airsim + remaining_agent + \
                   remaining_camera_gz + remaining_camera_airsim + remaining_viz + \
                   remaining_detection + remaining_tracking + remaining_guidance + remaining_rviz))

if [ $total_remaining -eq 0 ]; then
    echo -e "${GREEN}✓ All simulation processes successfully terminated${NC}"
else
    echo -e "${YELLOW}Warning: Some processes may still be running${NC}"
    [ $remaining_px4 -gt 0 ] && echo -e "${RED}  - $remaining_px4 PX4 process(es)${NC}"
    [ $remaining_gz -gt 0 ] && echo -e "${RED}  - $remaining_gz Gazebo/Ignition process(es)${NC}"
    [ $remaining_airsim -gt 0 ] && echo -e "${RED}  - $remaining_airsim AirSim/Unreal process(es)${NC}"
    [ $remaining_agent -gt 0 ] && echo -e "${RED}  - $remaining_agent MicroXRCE Agent process(es)${NC}"
    [ $remaining_camera_gz -gt 0 ] && echo -e "${RED}  - $remaining_camera_gz Gazebo Camera Bridge process(es)${NC}"
    [ $remaining_camera_airsim -gt 0 ] && echo -e "${RED}  - $remaining_camera_airsim AirSim Camera Bridge process(es)${NC}"
    [ $remaining_viz -gt 0 ] && echo -e "${RED}  - $remaining_viz Debug Translator process(es)${NC}"
    [ $remaining_detection -gt 0 ] && echo -e "${RED}  - $remaining_detection Detection Node process(es)${NC}"
    [ $remaining_tracking -gt 0 ] && echo -e "${RED}  - $remaining_tracking Tracking Node process(es)${NC}"
    [ $remaining_guidance -gt 0 ] && echo -e "${RED}  - $remaining_guidance Guidance Node process(es)${NC}"
    [ $remaining_rviz -gt 0 ] && echo -e "${RED}  - $remaining_rviz RViz2 process(es)${NC}"
    echo ""
    echo -e "${YELLOW}Run this command to check:${NC}"
    echo -e "${YELLOW}ps aux | grep -E \"px4|gz|gazebo|ignition|AirSim|Blocks|UE4|MicroXRCE|airsim|detection_node|tracking_node|guidance_node|rviz2\"${NC}"
fi

echo ""
echo -e "${GREEN}Cleanup complete!${NC}"
echo -e "${CYAN}You can now restart the simulation with: ${GREEN}./scripts/launch.sh${NC}"
