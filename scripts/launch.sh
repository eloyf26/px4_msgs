#!/bin/bash
# Unified launcher wrapper for Halcon1 system
# This script provides a simple entry point to the Python-based unified launcher

# Exit on error
set -e

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get repository root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Show header
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Halcon1 Unified Simulation Launcher            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Error: python3 not found${NC}"
    echo -e "${YELLOW}  Install with: sudo apt install python3${NC}"
    exit 1
fi

# Check for ROS2 Humble
if [ ! -f "/opt/ros/humble/setup.bash" ]; then
    echo -e "${RED}✗ Error: ROS2 Humble not found${NC}"
    echo -e "${YELLOW}  Please install ROS2 Humble first${NC}"
    echo -e "${YELLOW}  See: https://docs.ros.org/en/humble/Installation.html${NC}"
    exit 1
fi

# Check if workspace is built
WS_SETUP="$REPO_ROOT/install/setup.bash"
if [ ! -f "$WS_SETUP" ]; then
    echo -e "${RED}✗ Error: ROS2 workspace not built${NC}"
    echo -e "${YELLOW}  Run setup first: ./setup.sh --gazebo${NC}"
    echo -e "${YELLOW}  Or for AirSim: ./setup.sh --airsim${NC}"
    echo -e "${YELLOW}  Or for both: ./setup.sh --full${NC}"
    exit 1
fi

# Path to Python launcher
LAUNCHER="$REPO_ROOT/src/ros2/simulation/common/launcher.py"

# Check if launcher exists
if [ ! -f "$LAUNCHER" ]; then
    echo -e "${RED}✗ Error: Launcher not found at $LAUNCHER${NC}"
    echo -e "${YELLOW}  Your repository may be corrupted. Try re-cloning.${NC}"
    exit 1
fi

# Make launcher executable
chmod +x "$LAUNCHER" 2>/dev/null || true

# Validation complete
echo -e "${GREEN}✓ Pre-flight checks passed${NC}"
echo ""

# Source ROS2 and workspace so Python launcher can use ros2 commands
source /opt/ros/humble/setup.bash
source "$WS_SETUP"

# Run the Python launcher with all arguments
# The launcher inherits the sourced ROS2 environment
exec python3 "$LAUNCHER" "$@"
