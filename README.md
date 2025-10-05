# Halcon1 - Autonomous Drone Interception System

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-green.svg)](https://docs.ros.org/en/humble/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org/)

Autonomous drone interception system with PX4 SITL integration and ROS2 pipeline.

## Overview

Halcon1 implements a three-stage pipeline for autonomous drone interception:

```
Detection (YOLOv11n) → Tracking (Camera Transform) → Guidance (Kalman + ProNav)
```

**Core principle:** The same code runs on Gazebo, AirSim, and real hardware without changes. Only the simulator/sensor backend changes - all Halcon1 nodes remain identical.

## Quick Start

### Prerequisites

- Ubuntu 22.04
- ROS2 Humble
- Python 3.10+

### Installation

```bash
# Clone repository with submodules
git clone --recursive https://github.com/eloyf26/halcon1-system.git
cd halcon1-system

# Install for Gazebo (recommended)
./setup.sh --gazebo

# OR install for AirSim
./setup.sh --airsim

# OR install both
./setup.sh --full
```

**Time:** ~15-20 minutes
**Details:** [Installation Guide](docs/INSTALLATION.md)

### Launch

**Gazebo:**
```bash
./scripts/launch.sh --sim gazebo --mode multi --debug
```

**AirSim:**
```bash
# Terminal 1: Start AirSim environment
~/AirSimEnvironments/Blocks/Blocks.sh

# Terminal 2: Start Halcon1
./scripts/launch.sh --sim airsim
```

**Launch options:**
- `--sim gazebo|airsim` - Simulator to use
- `--mode single|multi` - Single drone or ally vs enemy
- `--debug` - Enable RViz markers and debug visualization

### Verify

```bash
# Check topics are publishing
ros2 topic hz /camera/image        # ~30 Hz
ros2 topic hz /enemy/detection     # ~10 Hz
ros2 topic hz /enemy/pose          # ~10 Hz

# View camera feed
ros2 run rqt_image_view rqt_image_view
```

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ SIMULATOR / HARDWARE                                         │
│  Gazebo | AirSim | Real Hardware                            │
└────────────┬──────────────────────────┬──────────────────────┘
             │ MAVLink                  │ Camera Topics
             ↓                          ↓
┌─────────────────────┐      ┌─────────────────────────────────┐
│ PX4 SITL/Firmware   │      │ Camera Bridge                   │
│ (Flight Controller) │      │ (ros_gz/airsim/usb_cam)         │
└──────────┬──────────┘      └──────────┬──────────────────────┘
           │ uXRCE-DDS                  │
           ↓                            ↓
┌──────────────────────────────────────────────────────────────┐
│ ROS2 Network (Standard Topics)                               │
│  /fmu/out/vehicle_odometry, /fmu/in/trajectory_setpoint      │
│  /camera/image, /camera/camera_info                          │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌──────────────────────────────────────────────────────────────┐
│ Halcon1 Pipeline (Simulator-Agnostic)                        │
│                                                               │
│  detection_node → tracking_node → guidance_node              │
│  (YOLOv11n)       (Transforms)     (Kalman+ProNav)           │
└──────────────────────────────────────────────────────────────┘
```

**Data flow:**
1. Camera → YOLO detection (2D bounding box)
2. Detection + PX4 odometry → World coordinates (3D position)
3. Kalman filter prediction → ProNav guidance (acceleration commands)
4. Commands → PX4 → Motors

**See:** [Architecture](docs/ARCHITECTURE.md) for detailed diagram

## Project Structure

```
halcon1-system/
├── src/
│   ├── lib/                      # Shared libraries
│   │   ├── algorithms/           # Kalman filter, ProNav
│   │   ├── transforms/           # Coordinate transformations
│   │   └── common_types/         # Shared data structures
│   └── ros2/
│       ├── modules/              # Core Halcon1 modules
│       │   ├── detection/        # YOLO detection
│       │   ├── tracking/         # Coordinate transforms
│       │   ├── guidance/         # Kalman + ProNav
│       │   ├── msgs/             # Custom message definitions
│       │   ├── bringup/          # Launch files
│       │   └── debug/            # Visualization tools
│       ├── external/             # PX4 packages
│       │   └── px4_msgs/         # PX4 message definitions
│       └── simulation/           # Simulator-specific code
│           ├── common/           # SimulationEngine interface
│           ├── gazebo/           # Gazebo implementation
│           └── airsim/           # AirSim implementation
├── external/                     # Git submodules
│   ├── PX4-Autopilot/            # PX4 flight stack
│   └── Micro-XRCE-DDS-Agent/     # PX4-ROS2 bridge
├── scripts/                      # Launch and utility scripts
├── docs/                         # Comprehensive documentation
└── README.md                     # This file
```

## Documentation

**Getting Started:**
- [Installation](docs/INSTALLATION.md) - Setup instructions and troubleshooting
- [Scripts](docs/SCRIPTS.md) - Launch script options and usage

**Understanding the System:**
- [Architecture](docs/ARCHITECTURE.md) - System design and data flow
- [Algorithms](docs/ALGORITHMS.md) - Detection, tracking, and guidance details
- [Simulation](docs/SIMULATION.md) - How to add simulators or integrate real hardware

**Development:**
- [Development Guide](docs/DEVELOPMENT.md) - Building, testing, contributing

## Simulator Comparison

| Feature | Gazebo | AirSim |
|---------|--------|--------|
| **Setup** | 5 min | 15 min |
| **Graphics** | Good | Photo-realistic |
| **Best For** | Development | CV research |

See [Simulation Guide](docs/SIMULATION.md) for adding Isaac Sim or real hardware.

## License

Apache 2.0 - See [LICENSE](LICENSE)

## Built With

- [PX4 Autopilot](https://px4.io/) - Flight controller
- [Gazebo Harmonic](https://gazebosim.org/) - Simulator
- [Microsoft AirSim](https://microsoft.github.io/AirSim/) - Photo-realistic simulator
- [ROS2 Humble](https://ros.org/) - Middleware
- [Ultralytics YOLOv11](https://ultralytics.com/) - Object detection
