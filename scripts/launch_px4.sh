#!/bin/bash
# Launch PX4 SITL with X500 quadcopter with mono camera
# Using PX4's integrated Gazebo Harmonic

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../external/PX4-Autopilot"
export LIBGL_ALWAYS_SOFTWARE=1

echo "Starting PX4 SITL with X500 mono camera (Gazebo Harmonic)..."
make px4_sitl gz_x500_mono_cam