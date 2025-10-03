#!/bin/bash
# Clean up script for multi-drone simulation

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Cleaning up Multi-Drone Simulation ===${NC}"

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

# Kill simulation processes
echo -e "${YELLOW}Stopping PX4 instances...${NC}"
kill_process "px4"

echo -e "${YELLOW}Stopping MicroXRCE Agent...${NC}"
kill_process "MicroXRCEAgent"

echo -e "${YELLOW}Stopping Gazebo...${NC}"
kill_process "gz sim"
kill_process "gz gui"
kill_process "gzserver"
kill_process "gzclient"
kill_process "ruby.*gz"
kill_process "ign gazebo"
kill_process "ignition"
# Kill any Gazebo-related processes
pkill -f "gazebo" 2>/dev/null
pkill -f "gz" 2>/dev/null

echo -e "${YELLOW}Stopping ROS2 nodes...${NC}"
kill_process "ros2.*parameter_bridge"
kill_process "rqt_image_view"
kill_process "rviz2"
kill_process "enemy_offboard_control"
kill_process "px4_debug_translator"
kill_process "ros_gz_bridge"
kill_process "detection_node"
kill_process "tracking_node"

echo -e "${YELLOW}Stopping terminal emulators spawned by script...${NC}"
# Kill terminal windows with specific titles
kill_process "gnome-terminal.*MicroXRCE Agent"
kill_process "gnome-terminal.*Ally Drone"
kill_process "gnome-terminal.*Enemy Drone"
kill_process "gnome-terminal.*Camera Bridge"
kill_process "gnome-terminal.*Detection Node"
kill_process "gnome-terminal.*Tracking Node"
kill_process "gnome-terminal.*Camera Viewer"
kill_process "gnome-terminal.*RViz2"
kill_process "gnome-terminal.*Enemy Movement"
kill_process "gnome-terminal.*PX4 Debug Translator"

# Clean up any leftover shared memory or lock files
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -f /tmp/.X*lock 2>/dev/null
rm -rf /tmp/gz* 2>/dev/null
# Clean up any test detection images
rm -f /tmp/test_input.jpg 2>/dev/null
rm -f /tmp/test_annotated.jpg 2>/dev/null

# Check for remaining processes
echo -e "${GREEN}Checking for remaining processes...${NC}"
remaining_px4=$(pgrep -c px4)
remaining_gz=$(pgrep -c -f "gz\|gazebo\|ignition")
remaining_agent=$(pgrep -c MicroXRCEAgent)
remaining_detection=$(pgrep -c detection_node)
remaining_tracking=$(pgrep -c tracking_node)

if [ $remaining_px4 -eq 0 ] && [ $remaining_gz -eq 0 ] && [ $remaining_agent -eq 0 ] && [ $remaining_detection -eq 0 ] && [ $remaining_tracking -eq 0 ]; then
    echo -e "${GREEN}✓ All simulation processes successfully terminated${NC}"
else
    echo -e "${YELLOW}Warning: Some processes may still be running${NC}"
    [ $remaining_px4 -gt 0 ] && echo -e "${RED}  - $remaining_px4 PX4 process(es)${NC}"
    [ $remaining_gz -gt 0 ] && echo -e "${RED}  - $remaining_gz Gazebo/Ignition process(es)${NC}"
    [ $remaining_agent -gt 0 ] && echo -e "${RED}  - $remaining_agent MicroXRCE Agent process(es)${NC}"
    [ $remaining_detection -gt 0 ] && echo -e "${RED}  - $remaining_detection Detection Node process(es)${NC}"
    [ $remaining_tracking -gt 0 ] && echo -e "${RED}  - $remaining_tracking Tracking Node process(es)${NC}"
    echo -e "${YELLOW}Run 'ps aux | grep -E \"px4|gz|gazebo|ignition|MicroXRCE|detection_node|tracking_node\"' to check${NC}"
fi

echo -e "${GREEN}Cleanup complete!${NC}"