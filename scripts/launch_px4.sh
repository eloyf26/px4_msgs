#!/bin/bash
# Launch PX4 SITL with X500 quadcopter with mono camera
# First launch Gazebo, then connect PX4 to it

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PX4_DIR="$SCRIPT_DIR/../external/PX4-Autopilot"

echo "Starting Gazebo Fortress with X500 mono camera model..."
# Set Gazebo model path to include PX4 models
export GZ_SIM_RESOURCE_PATH="$PX4_DIR/Tools/simulation/gz/models:$GZ_SIM_RESOURCE_PATH"

# Launch Gazebo with empty world (in background)
gz sim -v4 -r empty.sdf &
GAZEBO_PID=$!

# Wait for Gazebo to start
echo "Waiting for Gazebo to initialize..."
sleep 5

# Spawn x500_mono_cam model in Gazebo
echo "Spawning x500_mono_cam model..."
gz service -s /world/empty/create \
  --reqtype ignition.msgs.EntityFactory \
  --reptype ignition.msgs.Boolean \
  --timeout 5000 \
  --req "sdf_filename: \"x500_mono_cam\", name: \"x500\""

# Now start PX4 SITL to connect to the spawned model
echo "Starting PX4 SITL to connect to Gazebo..."
cd "$PX4_DIR"
make px4_sitl_default

# If PX4 exits, clean up Gazebo
echo "Cleaning up Gazebo..."
kill $GAZEBO_PID 2>/dev/null