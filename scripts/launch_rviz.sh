#!/bin/bash

# Launch RViz2 with Halcon1 visualization configuration

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Starting RViz2 for Halcon1 visualization..."
echo "Topics to visualize:"
echo "  • /camera/image       - Camera feed"
echo "  • /enemy/pose         - Target position (if available)"
echo "  • /enemy/tracked      - Tracked target data"
echo "  • /predicted_trajectory - Predicted path"
echo "  • /interception/command - Interception target"
echo ""

# Source ROS2 environment
source /opt/ros/humble/setup.bash
source ../ws_ros2/install/setup.bash

# Launch RViz2 with custom config (if exists) or default
RVIZ_CONFIG="$SCRIPT_DIR/../config/halcon1_rviz.rviz"

if [ -f "$RVIZ_CONFIG" ]; then
    echo "→ Using custom RViz configuration..."
    rviz2 -d "$RVIZ_CONFIG"
else
    echo "→ Using default RViz configuration..."
    echo "  (You can save your configuration to config/halcon1_rviz.rviz)"
    rviz2
fi