#!/bin/bash

# Halcon1 Complete System Launcher
# Launches all processes in the correct order with proper timing

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=== Halcon1 Complete System Launch ==="
echo ""
echo "Usage:"
echo "  ./launch_all.sh           # Launch all components"
echo "  ./launch_all.sh --viz     # Launch all + RViz visualization"
echo "  ./launch_all.sh --help    # Show this help"
echo ""

# Parse command line arguments
LAUNCH_RVIZ=false

if [ "$1" = "--help" ]; then
    echo "This script launches all components in the correct order:"
    echo "  1. PX4 SITL with Gazebo (x500_mono_cam)"
    echo "  2. MicroXRCE Agent (PX4 ↔ ROS2 bridge)"
    echo "  3. Camera Bridge (Gazebo ↔ ROS2)"
    echo "  4. Halcon1 Pipeline (Detection → Tracking → Prediction → Interception)"
    echo "  5. RViz2 Visualization (if --viz flag used)"
    echo ""
    echo "Options:"
    echo "  --viz     Also launch RViz2 for visualization"
    echo "  --help    Show this help and exit"
    echo ""
    echo "Press Ctrl+C to stop all processes"
    echo ""
    exit 0
fi

if [ "$1" = "--viz" ]; then
    LAUNCH_RVIZ=true
    echo "🎯 Launching with visualization enabled"
fi

echo "This will launch all components in the correct order:"
echo "  1. PX4 SITL with Gazebo (x500_mono_cam)"
echo "  2. MicroXRCE Agent (PX4 ↔ ROS2 bridge)"
echo "  3. Camera Bridge (Gazebo ↔ ROS2)"
echo "  4. Halcon1 Pipeline (Detection → Tracking → Prediction → Interception)"
if [ "$LAUNCH_RVIZ" = true ]; then
    echo "  5. RViz2 Visualization"
fi
echo ""
echo "Press Ctrl+C to stop all processes"
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Shutting down all processes..."
    kill $(jobs -p) 2>/dev/null || true
    wait
    echo "All processes stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Source ROS2 environment
source /opt/ros/humble/setup.bash
source ws_ros2/install/setup.bash

# 1. Launch PX4 SITL with Gazebo
echo "→ [1/4] Starting PX4 SITL with Gazebo Harmonic..."
cd external/PX4-Autopilot
make px4_sitl gz_x500_mono_cam &
PX4_PID=$!
cd "$SCRIPT_DIR"

# Wait for PX4/Gazebo to initialize
echo "    Waiting for PX4/Gazebo to initialize (15 seconds)..."
sleep 15

# 2. Launch MicroXRCE Agent
echo "→ [2/4] Starting MicroXRCE Agent..."
cd external/Micro-XRCE-DDS-Agent/build
./MicroXRCEAgent udp4 -p 8888 &
AGENT_PID=$!
cd "$SCRIPT_DIR"

# Wait for agent connection
echo "    Waiting for MicroXRCE Agent to connect (5 seconds)..."
sleep 5

# 3. Launch Camera Bridge
echo "→ [3/4] Starting Camera Bridge..."
cd scripts
./launch_camera_bridge.sh &
BRIDGE_PID=$!
cd "$SCRIPT_DIR"

# Wait for bridge to establish
echo "    Waiting for Camera Bridge to establish (5 seconds)..."
sleep 5

# 4. Launch Halcon1 Pipeline
echo "→ [4/4] Starting Halcon1 Pipeline..."
cd ws_ros2
ros2 launch halcon1_bringup pipeline.launch.py &
PIPELINE_PID=$!
cd "$SCRIPT_DIR"

# Wait for pipeline to establish
echo "    Waiting for Halcon1 Pipeline to establish (5 seconds)..."
sleep 5

# 5. Launch RViz if requested
RVIZ_PID=""
if [ "$LAUNCH_RVIZ" = true ]; then
    echo "→ [5/5] Starting RViz2 Visualization..."
    cd scripts
    ./launch_rviz.sh &
    RVIZ_PID=$!
    cd "$SCRIPT_DIR"
    echo "    RViz2 launched, waiting for initialization (3 seconds)..."
    sleep 3
fi

echo ""
echo "✅ All systems launched successfully!"
echo ""
echo "🎯 System Status:"
echo "   • PX4 SITL:        Running (PID: $PX4_PID)"
echo "   • MicroXRCE Agent: Running (PID: $AGENT_PID)"
echo "   • Camera Bridge:   Running (PID: $BRIDGE_PID)"
echo "   • Halcon1 Pipeline: Running (PID: $PIPELINE_PID)"
if [ "$LAUNCH_RVIZ" = true ] && [ -n "$RVIZ_PID" ]; then
    echo "   • RViz2 Visualization: Running (PID: $RVIZ_PID)"
fi
echo ""
echo "📊 Available ROS2 Topics:"
echo "   • /camera/image       - Camera feed from drone"
echo "   • /camera/camera_info - Camera calibration"
echo "   • /enemy/detection    - Target detections @ 10Hz"
echo "   • /enemy/tracked      - Target tracking @ 10Hz"
echo "   • /enemy/predicted    - Trajectory predictions @ 10Hz"
echo "   • /interception/command - Interception commands @ 10Hz"
echo ""
echo "🖥️  Monitor with:"
echo "   • ros2 topic list"
echo "   • ros2 topic hz /enemy/detection"
echo "   • ros2 topic echo /enemy/tracked --once"
echo ""
echo "Press Ctrl+C to stop all processes..."

# Wait for all processes
wait