#!/bin/bash
# Launch PX4 SITL with custom X500 model
# Using PX4's integrated Gazebo Harmonic with custom models

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Export custom simulation resource path
export GZ_SIM_RESOURCE_PATH="$SCRIPT_DIR/../simulation:$GZ_SIM_RESOURCE_PATH"

# Navigate to PX4 directory
cd "$SCRIPT_DIR/../external/PX4-Autopilot"

# Disable GPU acceleration to avoid crashes
export LIBGL_ALWAYS_SOFTWARE=1

echo "Starting PX4 SITL with custom X500 model (Gazebo Harmonic)..."
echo "Custom models path: $SCRIPT_DIR/../simulation"

# Launch with the custom model using the registered airframe
make px4_sitl gz_x500_custom