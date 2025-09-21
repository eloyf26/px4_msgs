#!/bin/bash
# Launch MicroXRCE-DDS Agent

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../external/Micro-XRCE-DDS-Agent/build"

echo "Starting MicroXRCE-DDS Agent..."
./MicroXRCEAgent udp4 -p 8888