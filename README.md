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
./scripts/launch_halcon1.sh  # Terminal 3: Halcon1 Pipeline
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
git clone --recursive https://github.com/yourusername/halcon1-system.git
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
- Launches Gazebo with X500 quadcopter
- ⚠️ **Requires QGroundControl to be running**

**Terminal 2: MicroXRCE Agent**
```bash
./scripts/launch_agent.sh
```
- Bridges PX4 and ROS2 communication
- Runs on UDP port 8888

**Terminal 3: Halcon1 Pipeline**
```bash
./scripts/launch_halcon1.sh
# Or for offboard control demo:
./scripts/launch_offboard.sh
```
- Starts processing nodes or offboard control

### Monitor System (Terminal 4)

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

## License

Apache 2.0 - See LICENSE file

## Contributors

- Halcon Team

## Documentation

- [Testing Guide](TESTING.md) - Detailed testing procedures
- [PX4 Troubleshooting](PX4_FIX.md) - PX4 specific issues