#!/bin/bash
# Improved cleanup script for Halcon1 simulation
# Properly kills terminal windows spawned by the launcher

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Halcon1 Simulation Cleanup (Improved) ===${NC}"
echo -e "${CYAN}Cleaning up all simulation processes and terminal windows...${NC}"

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

# ============================================================================
# STEP 1: Kill the actual simulation processes first
# ============================================================================

echo -e "${YELLOW}[1/3] Stopping simulation processes...${NC}"

# Kill PX4 instances
kill_process "px4"

# Kill MicroXRCE Agent
kill_process "MicroXRCEAgent"

# Kill Gazebo processes
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
kill_process "Blocks"
kill_process "CityEnviron"
kill_process "LandscapeMountains"
kill_process "AirSim"
kill_process "UE4"
kill_process "UnrealEngine"

# Kill ROS2 bridge processes
kill_process "ros2.*parameter_bridge"
kill_process "ros_gz_bridge"
kill_process "camera_bridge"
kill_process "viz_translator"
kill_process "enemy_visualizer"
kill_process "ally_visualizer"
kill_process "enemy_control"

# Kill Halcon1 pipeline nodes
kill_process "detection_node"
kill_process "tracking_node"
kill_process "guidance_node"

# Kill visualization tools
kill_process "rqt_image_view"
kill_process "rviz2"

# ============================================================================
# STEP 2: Kill the bash wrapper processes (the ones stuck on 'read')
# ============================================================================

echo -e "${YELLOW}[2/3] Stopping terminal wrapper processes...${NC}"

# These are the bash processes spawned by gnome-terminal that run the colored headers
# They match the pattern: bash -c "echo -e '\033[...] ... read;"
kill_process "bash -c.*echo -e.*Press Enter to close"

# Alternative: Kill all bash processes that contain our ROS2 launch commands
kill_process "bash -c.*ros2 launch bringup"
kill_process "bash -c.*ros2 run.*visualizer"
kill_process "bash -c.*ros2 run enemy_control"
kill_process "bash -c.*MicroXRCEAgent"
kill_process "bash -c.*px4"

# ============================================================================
# STEP 3: Kill orphaned terminal windows
# ============================================================================

echo -e "${YELLOW}[3/3] Closing orphaned terminal windows...${NC}"

# Find gnome-terminal processes that might be orphaned
# These are terminals that were spawned by the launcher and are now empty
orphan_terminals=$(pgrep -f "gnome-terminal --title")
if [ ! -z "$orphan_terminals" ]; then
    echo -e "${YELLOW}Found orphaned terminal windows, closing them...${NC}"
    for pid in $orphan_terminals; do
        # Check if this terminal has any active child processes
        children=$(pgrep -P $pid 2>/dev/null | wc -l)
        if [ $children -eq 0 ] || [ $children -eq 1 ]; then
            # No children or only bash child (likely stuck on read)
            echo -e "${RED}Closing orphaned terminal PID $pid${NC}"
            kill -TERM $pid 2>/dev/null
            sleep 0.5
            kill -KILL $pid 2>/dev/null
        fi
    done
fi

# Force close any remaining gnome-terminal processes launched by the launcher
# (these will have been started by Python subprocess.Popen)
launcher_terminals=$(ps aux | grep "gnome-terminal" | grep -E "MicroXRCE|PX4|Camera|Pipeline|Visualizer|Enemy|RViz" | awk '{print $2}')
if [ ! -z "$launcher_terminals" ]; then
    echo -e "${YELLOW}Force closing launcher terminals: $launcher_terminals${NC}"
    for pid in $launcher_terminals; do
        kill -KILL $pid 2>/dev/null
    done
fi

# ============================================================================
# STEP 4: Clean up temporary files
# ============================================================================

echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -f /tmp/.X*lock 2>/dev/null
rm -rf /tmp/gz* 2>/dev/null
rm -rf /tmp/AirSim* 2>/dev/null
rm -f /tmp/test_input.jpg 2>/dev/null
rm -f /tmp/test_annotated.jpg 2>/dev/null

# ============================================================================
# STEP 5: Final verification
# ============================================================================

echo -e "${GREEN}Checking for remaining processes...${NC}"

remaining_px4=$(pgrep -c px4 2>/dev/null || echo 0)
remaining_gz=$(pgrep -c -f "gz\|gazebo\|ignition" 2>/dev/null || echo 0)
remaining_airsim=$(pgrep -c -f "Blocks\|CityEnviron\|LandscapeMountains\|AirSim\|UE4\|UnrealEngine" 2>/dev/null || echo 0)
remaining_agent=$(pgrep -c MicroXRCEAgent 2>/dev/null || echo 0)
remaining_ros=$(pgrep -c -f "ros2.*launch\|ros2.*run" 2>/dev/null || echo 0)
remaining_bash=$(pgrep -c -f "bash -c.*Press Enter to close" 2>/dev/null || echo 0)
remaining_terminals=$(pgrep -c -f "gnome-terminal.*--title" 2>/dev/null || echo 0)

# Calculate total remaining
total_remaining=$((remaining_px4 + remaining_gz + remaining_airsim + remaining_agent + remaining_ros + remaining_bash + remaining_terminals))

if [ $total_remaining -eq 0 ]; then
    echo -e "${GREEN}✓ All simulation processes and terminals successfully closed${NC}"
else
    echo -e "${YELLOW}Warning: Some processes may still be running${NC}"
    [ $remaining_px4 -gt 0 ] && echo -e "${RED}  - $remaining_px4 PX4 process(es)${NC}"
    [ $remaining_gz -gt 0 ] && echo -e "${RED}  - $remaining_gz Gazebo/Ignition process(es)${NC}"
    [ $remaining_airsim -gt 0 ] && echo -e "${RED}  - $remaining_airsim AirSim/Unreal process(es)${NC}"
    [ $remaining_agent -gt 0 ] && echo -e "${RED}  - $remaining_agent MicroXRCE Agent process(es)${NC}"
    [ $remaining_ros -gt 0 ] && echo -e "${RED}  - $remaining_ros ROS2 process(es)${NC}"
    [ $remaining_bash -gt 0 ] && echo -e "${RED}  - $remaining_bash stuck bash process(es)${NC}"
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
