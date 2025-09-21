#!/bin/bash
# Launch PX4 SITL with parameters for offboard control using environment variables
#
# Usage: ./launch_px4_offboard.sh [speed_factor]
#   speed_factor: Simulation speed (optional)
#                 1.0 = real-time (default)
#                 0.5 = half speed (good for debugging)
#                 0.1 = very slow (step-by-step debugging)
#                 2.0 = double speed (faster testing)
#
# Examples:
#   ./launch_px4_offboard.sh        # Run at normal speed
#   ./launch_px4_offboard.sh 0.5    # Run at half speed
#   ./launch_px4_offboard.sh 0.1    # Run very slow for debugging

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../external/PX4-Autopilot"

echo "========================================"
echo "Starting PX4 SITL for Offboard Control"
echo "========================================"
echo ""
echo "⚠️  IMPORTANT: QGroundControl must be connected!"
echo "   Please launch QGroundControl before running offboard control"
echo "   QGC acts as the Ground Control Station (GCS)"
echo ""

# Set minimal parameters for offboard control
export PX4_PARAM_COM_RCL_EXCEPT=4    # Allow offboard without RC
export PX4_PARAM_COM_ARM_WO_GPS=1    # Allow arming without GPS
export PX4_PARAM_COM_OBL_RC_ACT=0    # Disable RC loss action in offboard
export PX4_PARAM_NAV_DLL_ACT=0       # Disable data link loss action

# Set simulation speed (1 = realtime)
# Can be overridden by environment variable or command line argument
SIM_SPEED=${1:-${PX4_SIM_SPEED_FACTOR:-1}}
export PX4_SIM_SPEED_FACTOR=$SIM_SPEED

echo "Parameters set:"
echo "  COM_RCL_EXCEPT=4 (Allow offboard without RC)"
echo "  COM_ARM_WO_GPS=1 (Allow arming without GPS)"
echo "  PX4_SIM_SPEED_FACTOR=$SIM_SPEED (Simulation speed: 1=realtime, <1=slower, >1=faster)"
echo ""
echo "Launching PX4 SITL..."
echo "----------------------------------------"

# Launch PX4 with the environment variables
make px4_sitl gz_x500