#!/bin/bash
# Launch PX4 SITL with multiple drones
# Using custom models and worlds without modifying PX4

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Export custom simulation resource path
export GZ_SIM_RESOURCE_PATH="$SCRIPT_DIR/../simulation:$GZ_SIM_RESOURCE_PATH"

# Navigate to PX4 directory
cd "$SCRIPT_DIR/../external/PX4-Autopilot"

# Disable GPU acceleration to avoid crashes
export LIBGL_ALWAYS_SOFTWARE=1

echo "Starting PX4 SITL with multiple drone support..."
echo "Custom models path: $SCRIPT_DIR/../simulation"

# Method 1: Launch with custom world file (when you create one)
# PX4_GZ_WORLD=$SCRIPT_DIR/../simulation/worlds/multi_drone.sdf make px4_sitl gz_x500_mono_cam

# Method 2: Launch default world but you can spawn additional models manually
# After launch, in another terminal you can use:
# gz service -s /world/default/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 --req 'sdf_filename: "model://x500_custom", name: "drone2", pose: {position: {x: 2, y: 0, z: 0.5}}'

make px4_sitl gz_x500_mono_cam