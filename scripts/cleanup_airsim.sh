#!/bin/bash
# Clean up script for AirSim simulation

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Cleaning up AirSim Simulation ===${NC}"

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

# Kill AirSim-specific processes
echo -e "${YELLOW}Stopping PX4 SITL...${NC}"
kill_process "px4"

echo -e "${YELLOW}Stopping MicroXRCE Agent...${NC}"
kill_process "MicroXRCEAgent"

echo -e "${YELLOW}Stopping AirSim processes...${NC}"
kill_process "Blocks"
kill_process "CityEnviron"
kill_process "LandscapeMountains"
kill_process "AirSim"
kill_process "UE4"
kill_process "UnrealEngine"

echo -e "${YELLOW}Stopping ROS2 nodes...${NC}"
kill_process "airsim_camera_bridge"
kill_process "airsim_viz_translator"
kill_process "rqt_image_view"
kill_process "rviz2"
kill_process "detection_node"
kill_process "tracking_node"
kill_process "guidance_node"

echo -e "${YELLOW}Stopping terminal emulators spawned by script...${NC}"
# Kill terminal windows with specific titles
kill_process "gnome-terminal.*MicroXRCE Agent"
kill_process "gnome-terminal.*PX4 SITL"
kill_process "gnome-terminal.*AirSim Camera Bridge"
kill_process "gnome-terminal.*PX4 Debug Translator"
kill_process "gnome-terminal.*RViz2"
kill_process "gnome-terminal.*Detection Node"
kill_process "gnome-terminal.*Tracking Node"
kill_process "gnome-terminal.*Guidance Node"

# Clean up any leftover shared memory or lock files
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -f /tmp/.X*lock 2>/dev/null
# Clean up any test detection images
rm -f /tmp/test_input.jpg 2>/dev/null
rm -f /tmp/test_annotated.jpg 2>/dev/null
# Clean AirSim temporary files
rm -rf /tmp/AirSim* 2>/dev/null

# Check for remaining processes
echo -e "${GREEN}Checking for remaining processes...${NC}"
remaining_px4=$(pgrep -c px4)
remaining_airsim=$(pgrep -c -f "Blocks\|CityEnviron\|LandscapeMountains\|AirSim\|UE4\|UnrealEngine")
remaining_agent=$(pgrep -c MicroXRCEAgent)
remaining_camera=$(pgrep -c airsim_camera_bridge)
remaining_viz=$(pgrep -c airsim_viz_translator)
remaining_detection=$(pgrep -c detection_node)
remaining_tracking=$(pgrep -c tracking_node)

if [ $remaining_px4 -eq 0 ] && [ $remaining_airsim -eq 0 ] && [ $remaining_agent -eq 0 ] && [ $remaining_camera -eq 0 ] && [ $remaining_viz -eq 0 ] && [ $remaining_detection -eq 0 ] && [ $remaining_tracking -eq 0 ]; then
    echo -e "${GREEN}✓ All simulation processes successfully terminated${NC}"
else
    echo -e "${YELLOW}Warning: Some processes may still be running${NC}"
    [ $remaining_px4 -gt 0 ] && echo -e "${RED}  - $remaining_px4 PX4 process(es)${NC}"
    [ $remaining_airsim -gt 0 ] && echo -e "${RED}  - $remaining_airsim AirSim/Unreal process(es)${NC}"
    [ $remaining_agent -gt 0 ] && echo -e "${RED}  - $remaining_agent MicroXRCE Agent process(es)${NC}"
    [ $remaining_camera -gt 0 ] && echo -e "${RED}  - $remaining_camera AirSim Camera Bridge process(es)${NC}"
    [ $remaining_viz -gt 0 ] && echo -e "${RED}  - $remaining_viz AirSim Viz Translator process(es)${NC}"
    [ $remaining_detection -gt 0 ] && echo -e "${RED}  - $remaining_detection Detection Node process(es)${NC}"
    [ $remaining_tracking -gt 0 ] && echo -e "${RED}  - $remaining_tracking Tracking Node process(es)${NC}"
    echo -e "${YELLOW}Run 'ps aux | grep -E \"px4|AirSim|Blocks|UE4|MicroXRCE|airsim|detection_node|tracking_node\"' to check${NC}"
fi

echo -e "${GREEN}Cleanup complete!${NC}"
