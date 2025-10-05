#!/bin/bash
# Rebuild script for Halcon1 ROS2 packages
# This script rebuilds all or specific ROS2 packages with proper dependency order

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Parse arguments
CLEAN=false
REBUILD_GAZEBO=false
REBUILD_AIRSIM=false
REBUILD_CORE=true
SPECIFIC_PACKAGES=()

show_help() {
    echo "Halcon1 ROS2 Package Rebuild Script"
    echo ""
    echo "Usage: ./scripts/rebuild.sh [OPTIONS] [PACKAGES...]"
    echo ""
    echo "Options:"
    echo "  --clean         Clean build/install/log before rebuilding"
    echo "  --gazebo        Rebuild Gazebo packages (ros_gz, gazebo_enemy_*, etc.)"
    echo "  --airsim        Rebuild AirSim packages (camera_bridge, airsim_enemy_*, etc.)"
    echo "  --all           Rebuild everything (Gazebo + AirSim + Core)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./scripts/rebuild.sh                    # Rebuild core packages only"
    echo "  ./scripts/rebuild.sh --clean            # Clean and rebuild core"
    echo "  ./scripts/rebuild.sh --gazebo           # Rebuild Gazebo packages"
    echo "  ./scripts/rebuild.sh --all              # Rebuild everything"
    echo "  ./scripts/rebuild.sh detection tracking # Rebuild specific packages"
    echo "  ./scripts/rebuild.sh --clean --all      # Clean and rebuild everything"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --gazebo)
            REBUILD_GAZEBO=true
            shift
            ;;
        --airsim)
            REBUILD_AIRSIM=true
            shift
            ;;
        --all)
            REBUILD_GAZEBO=true
            REBUILD_AIRSIM=true
            REBUILD_CORE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
        *)
            # Specific package names
            SPECIFIC_PACKAGES+=("$1")
            shift
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Halcon1 ROS2 Package Rebuild Script            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if workspace exists
if [ ! -f "install/setup.bash" ]; then
    echo -e "${RED}✗ Error: Workspace not built${NC}"
    echo -e "${YELLOW}  Run ./setup.sh first${NC}"
    exit 1
fi

# Clean if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}→ Cleaning build artifacts...${NC}"
    rm -rf build/ install/ log/
    echo -e "${GREEN}✓ Cleaned${NC}"
    echo ""
fi

# Source ROS2
echo -e "${BLUE}→ Sourcing ROS2 Humble...${NC}"
source /opt/ros/humble/setup.bash
export GZ_VERSION=harmonic
echo -e "${GREEN}✓ ROS2 environment ready${NC}"
echo ""

# If specific packages were provided, build only those
if [ ${#SPECIFIC_PACKAGES[@]} -gt 0 ]; then
    echo -e "${BLUE}→ Rebuilding specific packages: ${SPECIFIC_PACKAGES[*]}${NC}"
    for pkg in "${SPECIFIC_PACKAGES[@]}"; do
        echo -e "${YELLOW}  Building $pkg...${NC}"
        colcon build --packages-select "$pkg"
        source install/setup.bash
        echo -e "${GREEN}  ✓ $pkg built${NC}"
    done
    echo ""
    echo -e "${GREEN}✓ Rebuild complete${NC}"
    exit 0
fi

# Otherwise, rebuild based on flags
echo -e "${BLUE}→ Starting rebuild...${NC}"
echo ""

# 1. Always rebuild px4_msgs first (dependency of everything)
echo -e "${YELLOW}→ Building px4_msgs...${NC}"
colcon build --packages-select px4_msgs
source install/setup.bash
echo -e "${GREEN}✓ px4_msgs built${NC}"
echo ""

# 2. Rebuild Gazebo packages if requested
if [ "$REBUILD_GAZEBO" = true ]; then
    echo -e "${YELLOW}→ Building Gazebo packages...${NC}"

    colcon build --packages-select ros_gz_interfaces
    source install/setup.bash

    colcon build --packages-select ros_gz_sim
    source install/setup.bash

    colcon build --packages-select ros_gz_bridge
    source install/setup.bash

    colcon build --packages-select ros_gz_image
    source install/setup.bash

    colcon build --packages-select ros_gz_sim_demos
    source install/setup.bash

    colcon build --packages-select ros_gz
    source install/setup.bash

    echo -e "${GREEN}✓ ros_gz packages built${NC}"
    echo ""
fi

# 3. Rebuild core packages
if [ "$REBUILD_CORE" = true ]; then
    echo -e "${YELLOW}→ Building core packages...${NC}"

    colcon build --packages-select msgs
    source install/setup.bash

    colcon build --packages-select common_types transforms algorithms
    source install/setup.bash

    colcon build --packages-select detection tracking guidance
    source install/setup.bash

    colcon build --packages-select ally_visualizer
    source install/setup.bash

    colcon build --packages-select bringup
    source install/setup.bash

    echo -e "${GREEN}✓ Core packages built${NC}"
    echo ""
fi

# 4. Rebuild Gazebo simulation packages if requested
if [ "$REBUILD_GAZEBO" = true ]; then
    echo -e "${YELLOW}→ Building Gazebo simulation packages...${NC}"

    colcon build --packages-select gazebo_enemy_control
    source install/setup.bash

    colcon build --packages-select gazebo_enemy_visualizer
    source install/setup.bash

    echo -e "${GREEN}✓ Gazebo simulation packages built${NC}"
    echo ""
fi

# 5. Rebuild AirSim packages if requested
if [ "$REBUILD_AIRSIM" = true ]; then
    echo -e "${YELLOW}→ Building AirSim packages...${NC}"

    colcon build --packages-select camera_bridge
    source install/setup.bash

    colcon build --packages-select airsim_enemy_control
    source install/setup.bash

    colcon build --packages-select airsim_enemy_visualizer
    source install/setup.bash

    echo -e "${GREEN}✓ AirSim packages built${NC}"
    echo ""
fi

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Rebuild Complete!                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Source the workspace in new terminals:${NC}"
echo -e "  source install/setup.bash"
echo ""
