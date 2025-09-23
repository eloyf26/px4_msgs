# Halcon1 System

Complete autonomous drone interception system with PX4 SITL integration and ROS2 pipeline.

## Overview

Halcon1 implements a four-stage pipeline for autonomous drone interception:
**Detection → Tracking → Prediction → Interception**

This repository contains all components needed to run the complete system, including simulation, communication bridges, and the processing pipeline.

## Quick Start

```bash
# Clone repository with submodules
git clone --recursive https://github.com/eloyf26/halcon1-system.git
cd halcon1-system

# Run setup (builds everything)
./setup.sh

# Launch system (3 terminals)
./scripts/launch_px4_offboard.sh      # Terminal 1: PX4 SITL
./scripts/launch_agent.sh    # Terminal 2: MicroXRCE Agent
./scripts/launch_camera_bridge.sh # Terminal 3: Camera Bridge
./scripts/launch_halcon1.sh  # Terminal 4: Halcon1 Pipeline
```

If you want to visualize the images captured by the simulated mono-camera you can run:

```bash
ros2 run rqt_image_view rqt_image_view
# Select /camera/image topic
```

You can also visualize the feed of any of the available ros2 topics:

```bash
ros2 topic echo /camera/camera_info --once
ros2 topic echo /enemy/detection --once
ros2 topic echo /enemy/tracked --once
ros2 topic echo /enemy/predicted --once
ros2 topic echo /interception/command --once
```

## Repository Structure

```
halcon1-system/
├── external/                    # External dependencies (git submodules)
│   ├── PX4-Autopilot/          # PX4 flight stack for SITL
│   └── Micro-XRCE-DDS-Agent/  # DDS communication bridge
├── ws_ros2/                    # ROS2 workspace
│   └── src/
│       ├── Halcon1/            # Core Halcon1 packages
│       │   ├── halcon1_msgs/  # Message definitions
│       │   ├── modules/        # Processing modules
│       │   │   ├── halcon1_detection/
│       │   │   ├── halcon1_tracking/
│       │   │   ├── halcon1_prediction/
│       │   │   └── halcon1_interception/
│       │   └── halcon1_bringup/  # Launch configurations
│       ├── px4_msgs/           # PX4 message definitions
│       ├── px4_ros_com/        # PX4-ROS2 bridge
│       └── px4_offboard/       # PX4 offboard examples
├── scripts/                    # Launch scripts
│   ├── launch_px4.sh          # Start PX4 SITL
│   ├── launch_agent.sh        # Start MicroXRCE Agent
│   └── launch_halcon1.sh     # Start Halcon1 pipeline
├── setup.sh                   # One-click setup script
└── README.md                  # This file
```

## Installation

### Prerequisites

- Ubuntu 22.04 (recommended)
- ROS2 Humble
- Python 3.10+
- CMake 3.16+

### Setup Instructions

1. **Clone the repository:**

```bash
git clone --recursive https://github.com/eloyf26/halcon1-system.git
cd halcon1-system
```

2. **Run the setup script:**

```bash
./setup.sh
```

This will:
- Initialize git submodules
- Build MicroXRCE-DDS-Agent
- Build PX4 SITL (optional)
- Install ROS2
- Install ROS2 Gazebo Bridge
- Build all ROS2 packages

## Running the System

### Setup Requirements

**QGroundControl (Required)**
- Download from: https://qgroundcontrol.com/
- Launch QGC before or after starting PX4
- Acts as Ground Control Station (prevents "No connection to GCS" errors)

### Three-Terminal Setup

**Terminal 1: PX4 SITL**

```bash
./scripts/launch_px4.sh
# Or for offboard control:
./scripts/launch_px4_offboard.sh
```
- Launches Gazebo with X500 quadcopter and mono camera
- ⚠️ **Requires QGroundControl to be running**

**Terminal 2: MicroXRCE Agent**

```bash
./scripts/launch_agent.sh
```
- Bridges PX4 and ROS2 communication
- Runs on UDP port 8888

**Termianl 3: Camera Bridge**

```bash
./scripts/launch_camera_bridge.sh
```

- Bridges Gazebo camera to ROS2 `/camera/image` topic

**Terminal 4: Halcon1 Pipeline**

```bash
./scripts/launch_halcon1.sh
# Or for offboard control demo:
./scripts/launch_offboard.sh
```
- Starts processing nodes or offboard control

### Monitor System (Terminal 5)

```bash
# Source workspace
source ws_ros2/install/setup.bash

# Check topic rates
ros2 topic hz /enemy/detection    # Should show ~10 Hz
ros2 topic hz /enemy/tracked      # Should show ~10 Hz

# View data flow
ros2 topic echo /enemy/detection --once
ros2 topic echo /interception/command --once

# List all topics
ros2 topic list

# Visualize mono camera ros2 node feed
ros2 run rqt_image_view rqt_image_view # Select /camera/image topic
```

## Pipeline Modules

### Detection Module (`halcon1_detection`)
- **Current**: Fabricates moving target detections
- **Output**: 2D pixel coordinates @ 10Hz
- **Future**: YOLO-based visual detection

### Tracking Module (`halcon1_tracking`)
- **Current**: Simple 2D→3D conversion
- **Output**: 3D position + velocity @ 10Hz
- **Future**: Kalman filter with camera calibration

### Prediction Module (`halcon1_prediction`)
- **Current**: Linear trajectory extrapolation
- **Output**: Future positions @ 10Hz
- **Future**: Monte Carlo uncertainty propagation

### Interception Module (`halcon1_interception`)
- **Current**: Direct path to predicted position
- **Output**: Target coordinates @ 10Hz
- **Future**: Optimized trajectory planning

## Data Flow

```
Camera (simulated) → /enemy/detection (x,y pixels @ 10Hz)
                  ↓
                  → /enemy/tracked (x,y,z meters @ 10Hz)
                  ↓
                  → /enemy/predicted (trajectory @ 10Hz)
                  ↓
                  → /interception/command (target @ 10Hz)
```

## Development

### Building Individual Packages

```bash
cd ws_ros2
source /opt/ros/humble/setup.bash
colcon build --packages-select halcon1_detection
```

### Testing Changes

```bash
# Rebuild and test
colcon build --packages-select <package_name>
source install/setup.bash
ros2 launch halcon1_bringup pipeline.launch.py
```

This spins up your ros2 node. Once it is spinned up you can feed it data by publishing to it's subscribed topics:

```bash
# Example: Publish fake detection
ros2 topic pub /enemy/detection halcon1_msgs/Detection '{header: {stamp: {sec: 0, nanosec: 0}, frame_id: "camera_frame"}, x: 320.0, y: 240.0}'
# Check output
ros2 topic echo /enemy/tracked --once
```

## Troubleshooting

### PX4 Build Issues

```bash
cd external/PX4-Autopilot
rm -rf build
git submodule update --init --recursive
make px4_sitl gz_x500
```

### MicroXRCE Connection Issues

```bash
# Kill existing agents
pkill MicroXRCEAgent
# Restart
./scripts/launch_agent.sh
```

### ROS2 Build Issues

```bash
cd ws_ros2
rm -rf build install log
colcon build
```

### Mono Camera Issue

If you can't see the camera feed in `rqt_image_view`, follow these steps to diagnose the issue:

1. Verify Gazebo is running the x500_mono_cam model.
2. Verify that gazebo is publishing 2 gz topics for the camera by running this command:
```bash
gz topic --list | grep camera
```
You should see something like:
```
/camera/camera_info
/camera/image
```
3. Verify that the camera bridge is converting those topics into ros2 topics by running:
```bash
ros2 topic list | grep camera
```
You should see:
```
/camera/camera_info
/camera/image
```
4. Echo one of the topics to see if data is being published:
```bash
ros2 topic echo /camera/camera_info --once
```
You should see camera calibration info data.

Most probably you will find the issue in step 4 (everything looks good but ros2 topic doesn't get any data published). If
you do, the reason is a missmatch in your gazebo and ros2 installation. PX4 is only compatible with Gazebo Harmonic, on the
other hand we use ROS2 Humble, which can bridge Gazebo Fortress out of the box. To bridge Gazebo Harmonic with ROS2 Humble
you need to build `ros_gz` package from source, from the custom `humble` branch. Then install some `ros_dep` pacakges that
provide linking between `ros_gz` and `gazebo_ros_pkgs`. Finally, you need to build `ros_gz` using `colcon`. All these steps
are included in `setup.sh` so if you run it again it should fix the issue. Otherwise, you may have conflicting installations
that are preventing setup from running properly. In that case try to uninstall them manually or start over with a clean
Ubuntu 22.04 machine.

## License

Apache 2.0 - See LICENSE file

## Contributors

- Halcon Team

## Documentation

- [Testing Guide](TESTING.md) - Detailed testing procedures
- [PX4 Troubleshooting](PX4_FIX.md) - PX4 specific issues