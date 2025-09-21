#!/bin/bash
# Launch PX4 SITL with parameters for offboard control using environment variables

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

# Set simulation speed (1 = realtime)
export PX4_SIM_SPEED_FACTOR=1

echo "Parameters set:"
echo "  COM_RCL_EXCEPT=4 (Allow offboard without RC)"
echo "  COM_ARM_WO_GPS=1 (Allow arming without GPS)"
echo ""
echo "Launching PX4 SITL..."
echo "----------------------------------------"

# Launch PX4 with the environment variables
make px4_sitl gz_x500