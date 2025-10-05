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

# Kill terminal wrapper processes (bash processes stuck on 'read')
echo -e "${YELLOW}Stopping terminal wrapper processes...${NC}"
# These are the bash processes spawned by gnome-terminal with our colored headers
kill_process "bash -c.*echo -e.*Press Enter to close"

# Kill bash processes containing our launcher commands
kill_process "bash -c.*ros2 launch bringup"
kill_process "bash -c.*ros2 run.*visualizer"
kill_process "bash -c.*ros2 run enemy_control"
kill_process "bash -c.*ros2 run.*bridge"
kill_process "bash -c.*MicroXRCEAgent"
kill_process "bash -c.*px4"

# Close orphaned terminal windows
echo -e "${YELLOW}Closing orphaned terminal windows...${NC}"
orphan_terminals=$(pgrep -f "gnome-terminal --title" 2>/dev/null)
if [ ! -z "$orphan_terminals" ]; then
    for pid in $orphan_terminals; do
        children=$(pgrep -P $pid 2>/dev/null | wc -l)
        if [ $children -eq 0 ] || [ $children -eq 1 ]; then
            kill -TERM $pid 2>/dev/null
            sleep 0.5
            kill -KILL $pid 2>/dev/null
        fi
    done
fi

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
remaining_px4=$(pgrep -c px4 2>/dev/null) || remaining_px4=0
remaining_gz=$(pgrep -c -f "gz\|gazebo\|ignition" 2>/dev/null) || remaining_gz=0
remaining_airsim=$(pgrep -c -f "Blocks\|CityEnviron\|LandscapeMountains\|AirSim\|UE4\|UnrealEngine" 2>/dev/null) || remaining_airsim=0
remaining_agent=$(pgrep -c MicroXRCEAgent 2>/dev/null) || remaining_agent=0
remaining_ros=$(pgrep -c -f "ros2.*launch\|ros2.*run.*visualizer\|ros2.*run.*bridge\|ros2.*run enemy_control" 2>/dev/null) || remaining_ros=0
remaining_detection=$(pgrep -c detection_node 2>/dev/null) || remaining_detection=0
remaining_tracking=$(pgrep -c tracking_node 2>/dev/null) || remaining_tracking=0
remaining_guidance=$(pgrep -c guidance_node 2>/dev/null) || remaining_guidance=0
remaining_rviz=$(pgrep -c rviz2 2>/dev/null) || remaining_rviz=0
remaining_bash=$(pgrep -c -f "bash -c.*Press Enter to close" 2>/dev/null) || remaining_bash=0
remaining_terminals=$(pgrep -c -f "gnome-terminal.*--title" 2>/dev/null) || remaining_terminals=0

# Calculate total remaining
total_remaining=$((remaining_px4 + remaining_gz + remaining_airsim + remaining_agent + remaining_ros + \
                   remaining_detection + remaining_tracking + remaining_guidance + remaining_rviz + \
                   remaining_bash + remaining_terminals))

if [ $total_remaining -eq 0 ]; then
    echo -e "${GREEN}✓ All simulation processes and terminals successfully closed${NC}"
else
    echo -e "${YELLOW}Warning: Some processes may still be running${NC}"
    [ $remaining_px4 -gt 0 ] && echo -e "${RED}  - $remaining_px4 PX4 process(es)${NC}"
    [ $remaining_gz -gt 0 ] && echo -e "${RED}  - $remaining_gz Gazebo/Ignition process(es)${NC}"
    [ $remaining_airsim -gt 0 ] && echo -e "${RED}  - $remaining_airsim AirSim/Unreal process(es)${NC}"
    [ $remaining_agent -gt 0 ] && echo -e "${RED}  - $remaining_agent MicroXRCE Agent process(es)${NC}"
    [ $remaining_ros -gt 0 ] && echo -e "${RED}  - $remaining_ros ROS2 process(es)${NC}"
    [ $remaining_detection -gt 0 ] && echo -e "${RED}  - $remaining_detection Detection Node process(es)${NC}"
    [ $remaining_tracking -gt 0 ] && echo -e "${RED}  - $remaining_tracking Tracking Node process(es)${NC}"
    [ $remaining_guidance -gt 0 ] && echo -e "${RED}  - $remaining_guidance Guidance Node process(es)${NC}"
    [ $remaining_rviz -gt 0 ] && echo -e "${RED}  - $remaining_rviz RViz2 process(es)${NC}"
    [ $remaining_bash -gt 0 ] && echo -e "${RED}  - $remaining_bash stuck bash wrapper(s)${NC}"
    [ $remaining_terminals -gt 0 ] && echo -e "${RED}  - $remaining_terminals terminal window(s)${NC}"
    echo ""
    echo -e "${YELLOW}Manual cleanup commands:${NC}"
    echo -e "${CYAN}  pkill -9 -f 'bash -c.*Press Enter to close'${NC}"
    echo -e "${CYAN}  pkill -9 -f 'gnome-terminal'${NC}"
    echo -e "${CYAN}  ps aux | grep -E 'px4|gz|ros2|bash -c' | grep -v grep${NC}"
fi

echo ""
echo -e "${GREEN}Cleanup complete!${NC}"
echo -e "${CYAN}You can now restart the simulation with: ${GREEN}./scripts/launch.sh${NC}"
