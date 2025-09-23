#!/bin/bash

# Halcon1 Quick Rebuild Script
# Rebuilds the ROS2 workspace after code changes

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=== Halcon1 Quick Rebuild ==="
echo ""
echo "Usage:"
echo "  ./rebuild.sh                    # Rebuild all packages"
echo "  ./rebuild.sh pkg1 pkg2         # Rebuild specific packages"
echo "  ./rebuild.sh --auto             # Auto-detect changed packages from git"
echo "  ./rebuild.sh --help             # Show this help"
echo ""

# Parse command line arguments
if [ "$1" = "--help" ]; then
    echo "Available packages:"
    echo "  ros_gz, halcon1_msgs, px4_msgs, px4_ros_com"
    echo "  halcon1_detection, halcon1_tracking, halcon1_prediction"
    echo "  halcon1_interception, halcon1_bringup, px4_offboard"
    echo ""
    exit 0
fi

cd ws_ros2
source /opt/ros/humble/setup.bash

# Auto-detect changed packages from git diff
if [ "$1" = "--auto" ]; then
    echo "→ Auto-detecting changed packages from git diff..."

    # Get list of changed files
    CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null || git diff --name-only --staged 2>/dev/null || echo "")

    if [ -z "$CHANGED_FILES" ]; then
        echo "  No changes detected, rebuilding all packages..."
        PACKAGES_TO_BUILD="all"
    else
        echo "  Changed files:"
        echo "$CHANGED_FILES" | sed 's/^/    /'

        # Map files to packages
        PACKAGES_TO_BUILD=""

        # Check each package directory
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/Halcon1/halcon1_msgs/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD halcon1_msgs"
        fi
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/Halcon1/modules/halcon1_detection/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD halcon1_detection"
        fi
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/Halcon1/modules/halcon1_tracking/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD halcon1_tracking"
        fi
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/Halcon1/modules/halcon1_prediction/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD halcon1_prediction"
        fi
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/Halcon1/modules/halcon1_interception/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD halcon1_interception"
        fi
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/Halcon1/halcon1_bringup/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD halcon1_bringup"
        fi
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/px4_msgs/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD px4_msgs"
        fi
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/px4_ros_com/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD px4_ros_com"
        fi
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/px4_offboard/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD px4_offboard"
        fi
        if echo "$CHANGED_FILES" | grep -q "ws_ros2/src/ros_gz/"; then
            PACKAGES_TO_BUILD="$PACKAGES_TO_BUILD ros_gz"
        fi

        if [ -z "$PACKAGES_TO_BUILD" ]; then
            echo "  No ROS2 packages affected, rebuilding all to be safe..."
            PACKAGES_TO_BUILD="all"
        else
            echo "  Detected packages to rebuild:$PACKAGES_TO_BUILD"
        fi
    fi
elif [ $# -eq 0 ]; then
    # No arguments - rebuild all packages
    PACKAGES_TO_BUILD="all"
else
    # Specific packages provided
    PACKAGES_TO_BUILD="$@"
fi

# Build packages
if [ "$PACKAGES_TO_BUILD" = "all" ]; then
    echo "→ Rebuilding all packages in dependency order..."
    colcon build --packages-select ros_gz
    colcon build --packages-select halcon1_msgs
    colcon build --packages-select px4_msgs px4_ros_com
    colcon build --packages-select halcon1_detection halcon1_tracking halcon1_prediction halcon1_interception
    colcon build --packages-select halcon1_bringup px4_offboard
else
    echo "→ Rebuilding specific packages: $PACKAGES_TO_BUILD"
    for package in $PACKAGES_TO_BUILD; do
        echo "  Building: $package"
        colcon build --packages-select "$package"
    done
fi

echo "✓ Rebuild complete!"
echo ""
echo "Don't forget to source the workspace in your terminals:"
echo "  source ws_ros2/install/setup.bash"
echo ""
echo "Or restart your launch scripts to pick up the changes."