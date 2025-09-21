#!/bin/bash
# Launch PX4 SITL with X500 quadcopter

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../external/PX4-Autopilot"

echo "Starting PX4 SITL with X500..."
make px4_sitl gz_x500