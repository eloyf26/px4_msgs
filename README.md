# Halcon1 - Autonomous Drone Interception System

Complete autonomous drone interception system with simulation support (Gazebo, AirSim) and PX4 integration.

## Overview

Halcon1 implements a three-stage pipeline for autonomous drone interception:

**Detection → Tracking → Guidance**

**Key Features:**
- 🎯 YOLO-based drone detection
- 📍 Camera-to-world coordinate transformation
- 🚀 Kalman Filter + Proportional Navigation guidance
- 🔄 Simulator-agnostic architecture (Gazebo, AirSim, Isaac Sim)
- ✈️ PX4 flight controller integration (works on real hardware!)

## Quick Start

### Prerequisites

- Ubuntu 22.04
- ROS2 Humble
- Python 3.10+
- ~2GB disk space

### 1. Install

```bash
# Clone with submodules
git clone --recursive https://github.com/eloyf26/halcon1-system.git
cd halcon1-system

# Setup for Gazebo (fast, lightweight)
./setup.sh --gazebo

# OR setup for AirSim (photo-realistic)
./setup.sh --airsim

# OR setup for both
./setup.sh --full
```

### 2. Launch Simulation

**Gazebo (Recommended for Development)**
```bash
./scripts/launch.sh --sim gazebo
```

**AirSim (Photo-Realistic)**
```bash
# First, launch AirSim environment manually:
cd ~/AirSimEnvironments/Blocks/
./Blocks.sh

# Then launch Halcon1:
./scripts/launch.sh --sim airsim
```

**With Debug Mode (RViz2)**
```bash
./scripts/launch.sh --sim gazebo --debug
```

**Multi-Drone (Ally vs Enemy)**
```bash
./scripts/launch.sh --sim gazebo --mode multi
```

### 3. Monitor System

```bash
# View camera feed
ros2 run rqt_image_view rqt_image_view

# Check detection output
ros2 topic echo /enemy/detection

# Check tracking output
ros2 topic echo /enemy/tracked

# Check guidance commands
ros2 topic echo /fmu/in/trajectory_setpoint
```

## System Architecture

Halcon1 uses a **simulator-agnostic** architecture:

```
┌─────────────────────────────────────────────────────────────┐
│ Halcon1 ROS2 Nodes (SAME CODE for all environments!)      │
│  - Detection: YOLO drone detection                         │
│  - Tracking: Camera → world coordinate transform           │
│  - Guidance: Kalman Filter + Proportional Navigation       │
└────────────┬────────────────────────────────────────────────┘
             │ Standard ROS2 Topics
             │ (/camera/image, /fmu/in/*, /fmu/out/*)
             ↓
┌─────────────────────────────────────────────────────────────┐
│ Simulation Engine (Gazebo OR AirSim OR Isaac OR Hardware) │
│  - Physics simulation                                       │
│  - Sensor simulation (camera, IMU, GPS)                    │
│  - PX4 SITL connection                                     │
└──────────────────────────────────────────────────────────────┘
```

**Key Insight**: Your detection, tracking, and guidance code works identically in simulation and real hardware!

## Documentation

### Getting Started
- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions
- [Simulation Guide](docs/SIMULATION.md) - How to use simulators

### Understanding the System
- [Architecture](docs/ARCHITECTURE.md) - System design and data flow
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and extending

### Simulator-Specific
- [Gazebo Setup](simulation/gazebo/README.md) - Fast, lightweight simulator
- [AirSim Setup](simulation/airsim/README.md) - Photo-realistic simulator
- [Isaac Sim Plans](simulation/isaac/README.md) - GPU-accelerated (planned)

## Repository Structure

```
halcon1-system/
├── simulation/              # Simulation engine implementations
│   ├── common/             # Unified launcher + interfaces
│   ├── gazebo/             # Gazebo-specific config
│   ├── airsim/             # AirSim-specific config
│   └── isaac/              # Isaac Sim (planned)
├── ws_ros2/src/
│   ├── Halcon1/            # Core logic (detection, tracking, guidance)
│   ├── px4_bridges/        # PX4 communication packages
│   └── simulation_bridges/ # Simulator-specific ROS2 bridges
├── external/
│   ├── PX4-Autopilot/      # PX4 flight stack (submodule)
│   └── Micro-XRCE-DDS-Agent/ # PX4-ROS2 bridge (submodule)
├── scripts/
│   └── launch_unified.sh   # Main launcher script
└── docs/                   # Detailed documentation
```

## Simulation Comparison

| Feature | Gazebo | AirSim | Isaac Sim* |
|---------|--------|--------|------------|
| **Setup Time** | 5 min | 10 min | 15 min |
| **Disk Space** | 500MB | 2-8GB | 10GB |
| **Graphics** | Good | Photo-realistic | Ray-traced |
| **Performance** | Fast ⚡ | Moderate | Very Fast (GPU) |
| **Best For** | Development, CI/CD | CV research, demos | ML training |

*Isaac Sim support is planned (not yet implemented)

## Halcon1 Pipeline

The system operates in three stages:

### 1. Detection (`detection`)
- **Input**: `/camera/image` (RGB camera feed)
- **Algorithm**: YOLOv8 drone detection
- **Output**: `/enemy/detection` (2D bounding box, pixel coordinates)

### 2. Tracking (`tracking`)
- **Input**: `/enemy/detection` + `/camera/camera_info` + `/fmu/out/vehicle_odometry`
- **Algorithm**: Pinhole camera model for depth estimation
- **Output**: `/enemy/tracked` (3D position + velocity in world frame)

### 3. Guidance (`guidance`)
- **Input**: `/enemy/tracked` + `/fmu/out/vehicle_odometry`
- **Algorithm**: Kalman Filter (prediction) + Proportional Navigation (guidance)
- **Output**: `/fmu/in/trajectory_setpoint` (acceleration commands to PX4)

## Development

### Building Individual Packages

```bash
cd ws_ros2
source /opt/ros/humble/setup.bash

# Build specific package
colcon build --packages-select detection

# Build all Halcon1 packages
colcon build --packages-up-to bringup
```

### Testing Changes

```bash
# Rebuild package
cd ws_ros2
colcon build --packages-select tracking
source install/setup.bash

# Test with fake data
ros2 topic pub /enemy/detection msgs/Detection \
  '{header: {frame_id: "camera"}, x: 320.0, y: 240.0, confidence: 0.95}'

# Check output
ros2 topic echo /enemy/tracked --once
```

### Adding a New Simulator

Want to add Isaac Sim, Webots, or another simulator?

1. Implement `SimulationEngine` interface in `simulation/<your_sim>/<your_sim>_engine.py`
2. Register with factory: `SimulationEngineFactory.register_engine("yoursim", YourSimEngine)`
3. Test: `./scripts/launch.sh --sim yoursim`

See [simulation/common/README.md](simulation/common/README.md) for detailed instructions.

## Troubleshooting

### Gazebo Issues

```bash
# Camera bridge not working
cd ws_ros2
colcon build --packages-select ros_gz_bridge --cmake-clean-cache

# PX4 won't connect
cd external/PX4-Autopilot
make clean && make px4_sitl gz_x500_mono_cam
```

### AirSim Issues

```bash
# Can't connect to AirSim
# 1. Ensure AirSim is running (you see the drone in Unreal)
# 2. Check settings.json exists:
ls ~/Documents/AirSim/settings.json

# 3. Verify Python packages:
pip install airsim msgpack-rpc-python
```

### Available Parameters

The unified launcher supports the following options:

```bash
# Simulator selection (default: gazebo)
--sim gazebo          # Fast, lightweight simulator
--sim airsim          # Photo-realistic Unreal Engine simulator

# Mode selection (default: single)
--mode single         # Single ally drone only
--mode multi          # Ally + enemy drones (launches enemy offboard control)

# Debug mode (default: off)
--debug               # Launches RViz2 and enables debugging node publishing

# World/environment (default: default)
--world <name>        # Load specific world (simulator-specific)
```

**Examples:**
```bash
# Simple launch
./scripts/launch.sh --sim gazebo

# Multi-drone with debug
./scripts/launch.sh --sim gazebo --mode multi --debug

# Custom world
./scripts/launch.sh --sim gazebo --world custom_world
```

## Contributing

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for:
- Code structure guidelines
- How to add new modules
- Testing procedures
- Pull request process

## License

Apache 2.0 - See [LICENSE](LICENSE) file

## Citation

If you use Halcon1 in your research, please cite:

```bibtex
@misc{halcon1,
  title={Halcon1: Autonomous Drone Interception System},
  author={Halcon Team},
  year={2025},
  url={https://github.com/eloyf26/halcon1-system}
}
```

## Acknowledgments

Built with:
- [PX4 Autopilot](https://px4.io/) - Flight controller software
- [Gazebo](https://gazebosim.org/) - Robot simulator
- [Microsoft AirSim](https://microsoft.github.io/AirSim/) - Autonomous vehicle simulator
- [ROS2](https://ros.org/) - Robot Operating System

---

**Need Help?** Check [docs/](docs/) or open an [issue](https://github.com/eloyf26/halcon1-system/issues)

**Want to Contribute?** See [DEVELOPMENT.md](docs/DEVELOPMENT.md)
