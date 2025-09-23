#!/bin/bash
# Launch PX4 SITL with custom X500 model
# Using PX4's integrated Gazebo Harmonic with custom models

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Export custom simulation resource path - this makes our models available to Gazebo
export GZ_SIM_RESOURCE_PATH="$SCRIPT_DIR/../simulation:$GZ_SIM_RESOURCE_PATH"

# Navigate to PX4 directory
cd "$SCRIPT_DIR/../external/PX4-Autopilot"

# Disable GPU acceleration to avoid crashes
export LIBGL_ALWAYS_SOFTWARE=1

echo "Starting PX4 SITL with custom models..."
echo "Custom models path: $SCRIPT_DIR/../simulation"
echo "Using base x500_mono_cam airframe with custom model override"

# Use the existing x500_mono_cam airframe but override the model path
# PX4_GZ_MODEL allows us to specify our custom model without modifying PX4
PX4_GZ_MODEL=x500_custom make px4_sitl gz_x500_mono_cam