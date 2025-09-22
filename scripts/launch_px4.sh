#!/bin/bash
# Launch PX4 SITL with X500 quadcopter with mono camera

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../external/PX4-Autopilot"

echo "Starting PX4 SITL with X500 mono camera..."
make px4_sitl gz_x500_mono_cam