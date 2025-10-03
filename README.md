# Halcon1 System

Complete autonomous drone interception system with PX4 SITL integration and ROS2 pipeline.

## Overview

Halcon1 implements a three-stage pipeline for autonomous drone interception:
**Detection → Tracking → Guidance**

This repository contains all components needed to run the complete system, including simulation, communication bridges, and the processing pipeline.

## Quick Start

### Single Drone Simulation

```bash
# Clone repository with submodules
git clone --recursive https://github.com/eloyf26/halcon1-system.git
cd halcon1-system

# Run setup (builds everything)
./setup.sh

# Launch system (4 terminals)
./scripts/launch_px4_offboard.sh      # Terminal 1: PX4 SITL
./scripts/launch_agent.sh             # Terminal 2: MicroXRCE Agent
./scripts/launch_camera_bridge.sh     # Terminal 3: Camera Bridge
./scripts/launch_halcon1.sh           # Terminal 4: Halcon1 Pipeline
```

### Two-Drone Simulation (Ally vs Enemy)

For simulating both ally and enemy drones:

```bash
# Launch all terminals automatically
./scripts/launch_multi_terminal.sh
```

This launches **7-9 terminals/windows** in total:

#### Essential Terminals (Required for Testing)
1. **Ally Drone PX4** (Terminal 2) - Instance 0 with mono camera at position (0, 2, 0)
   - Shows PX4 console output for ally drone
   - Required for monitoring ally drone status

2. **Enemy Drone PX4** (Terminal 3) - Instance 1 at position (0, -2, 0)
   - Shows PX4 console output for enemy drone
   - **ACTION REQUIRED**: Manually run `commander arm -f` then `commander takeoff`

3. **Camera Bridge** (Terminal 4) - Bridges ally camera to ROS2 topics
   - Converts Gazebo camera topics to ROS2 `/camera/image` and `/camera/camera_info`
   - Required for visual pipeline

4. **Enemy Movement Control** (Terminal 6) - Interactive enemy control
   - Shows movement selection menu after enemy is armed/airborne
   - Required to start enemy movement patterns

5. **Gazebo Window** - 3D simulation environment
   - Visual confirmation of drone positions and movements
   - Can be minimized but shouldn't be closed

#### Optional/Debug Terminals (Not Required for Basic Testing)
6. **MicroXRCE Agents** (Terminal 1) - Two agents on ports 8888 (ally) and 8889 (enemy)
   - Can be hidden - only shows connection logs
   - Required running but doesn't need monitoring

7. **PX4 Debug Translator** (Terminal 5) - Translates PX4 debug topics
   - Optional - provides additional telemetry data
   - Can be closed if not debugging PX4 internals

8. **RViz Terminal** (Terminal 7, if launched) - Command terminal for RViz
   - Optional - only needed if using RViz visualization
   - Can be closed if not using RViz

9. **RViz Window** (if launched) - ROS2 3D visualization tool
   - Optional - for visualizing ROS2 topics like trajectories
   - More detailed than Gazebo for ROS2 data

#### Cleanup
To stop all running processes and terminals:
```bash
./scripts/cleanup_simulation.sh
```
This script kills all PX4, Gazebo, MicroXRCE agents, and ROS2 nodes.

### AirSim Simulation (Alternative to Gazebo)

Halcon1 also supports **AirSim + Unreal Engine** as an alternative simulation environment. AirSim provides photo-realistic graphics and high-fidelity physics simulation.

#### Why Use AirSim?

- **Photo-realistic environments**: Unreal Engine 4/5 graphics
- **Custom environments**: Cities, buildings, complex terrain
- **Better camera simulation**: Realistic lighting, shadows, reflections
- **PhysX physics**: NVIDIA's physics engine
- **Same Halcon1 code**: No changes to detection/tracking/guidance nodes

#### Prerequisites

1. **AirSim Environment** (choose one):
   - Download prebuilt binary: [AirSim Releases](https://github.com/microsoft/AirSim/releases)
   - Recommended: Blocks environment (lightweight, good for testing)

2. **airsim_ros_pkgs**: ROS2 wrapper for AirSim
   ```bash
   cd ws_ros2/src
   git clone https://github.com/microsoft/airsim_ros_pkgs.git
   cd ../..
   colcon build --packages-select airsim_ros_pkgs
   ```

#### Quick Start with AirSim

1. **Configure AirSim**:
   ```bash
   # Copy configuration to AirSim directory
   mkdir -p ~/Documents/AirSim
   cp config/airsim/settings.json ~/Documents/AirSim/
   ```

2. **Start AirSim environment**:
   ```bash
   # Example: Blocks environment
   cd ~/AirSimEnvironments/Blocks
   ./LinuxBlocks.sh
   ```

3. **Launch Halcon1 with AirSim**:
   ```bash
   ./scripts/launch_airsim.sh
   ```

This launches 6 terminals:
1. **MicroXRCE Agent** - Same as Gazebo (UDP 8888)
2. **PX4 SITL** - Connects to AirSim via TCP 4560
3. **AirSim ROS Bridge** - Camera and sensor topics
4. **Detection Node** - YOLOv11n (unchanged)
5. **Tracking Node** - Coordinate transform (unchanged)
6. **Guidance Node** - Kalman Filter + ProNav (unchanged)

#### AirSim vs Gazebo Comparison

| Feature | Gazebo | AirSim |
|---------|--------|--------|
| **Graphics** | Ogre2 | Unreal Engine 4/5 |
| **Physics** | ODE/Bullet | PhysX (NVIDIA) |
| **Camera Quality** | Good | Photo-realistic |
| **Performance** | Fast | Slower (GPU intensive) |
| **Custom Environments** | SDF files | Unreal Editor |
| **Setup Difficulty** | Easy | Moderate |
| **Halcon1 Code Changes** | None | None |

#### Controlling the Drones in AirSim

**Ally Drone (PX4):**
- Use QGroundControl (same as Gazebo)
- Or PX4 console: `commander arm && commander takeoff`

**Enemy Drone (SimpleFlight):**
- Press `F1` in AirSim for keyboard control
- Or use Python API:
  ```python
  import airsim
  client = airsim.MultirotorClient()
  client.confirmConnection()
  client.enableApiControl(True, "Enemy")
  client.armDisarm(True, "Enemy")
  client.takeoffAsync(vehicle_name="Enemy").join()
  ```

#### Detailed Setup Guide

For detailed AirSim installation and configuration instructions, see:
- **Architecture Details**: [PLAN.md](PLAN.md)
- **Configuration Guide**: [config/airsim/README.md](config/airsim/README.md)

### Visualization

Monitor camera feed:
```bash
ros2 run rqt_image_view rqt_image_view
# Select /camera/image topic
```

Monitor ROS2 topics:
```bash
ros2 topic echo /camera/camera_info --once
ros2 topic echo /enemy/detection --once
ros2 topic echo /enemy/tracked --once
ros2 topic echo /interception/command --once

# For multi-drone simulation
ros2 topic list | grep "^/fmu"  # Ally drone topics (instance 0, no namespace)
ros2 topic list | grep px4_1    # Enemy drone topics (instance 1, namespaced)

# Example ally drone topics (no namespace):
ros2 topic echo /fmu/out/vehicle_status_v1 --once
ros2 topic echo /fmu/in/offboard_control_mode --once

# Example enemy drone topics (namespaced):
ros2 topic echo /px4_1/fmu/out/vehicle_status_v1 --once
ros2 topic echo /px4_1/fmu/in/offboard_control_mode --once
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
│       │   │   ├── halcon1_guidance/
│       │   └── halcon1_bringup/  # Launch configurations
│       ├── px4_msgs/           # PX4 message definitions
│       ├── px4_ros_com/        # PX4-ROS2 bridge
│       ├── px4_offboard/       # PX4 offboard examples
│       └── multi_drone_sim/    # Multi-drone simulation package
├── scripts/                    # Launch scripts
│   ├── launch_px4.sh          # Start PX4 SITL
│   ├── launch_agent.sh        # Start MicroXRCE Agent
│   ├── launch_halcon1.sh     # Start Halcon1 pipeline
│   └── launch_multi_terminal.sh # Launch multi-drone simulation
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

**QGroundControl (Required for single drone)**
- Download from: https://qgroundcontrol.com/
- Launch QGC before or after starting PX4
- Acts as Ground Control Station (prevents "No connection to GCS" errors)
- Not required for multi-drone simulation

### Single Drone Setup (4 Terminals)

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

**Terminal 3: Camera Bridge**

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

### Multi-Drone Setup (Automated)

```bash
./scripts/launch_multi_terminal.sh
```

This script automatically:
1. Cleans up existing PX4/Gazebo processes
2. Launches two MicroXRCE agents (ports 8888, 8889)
3. Starts ally drone with camera (instance 0)
4. Starts enemy drone (instance 1)
5. Sets up camera bridge for ally drone
6. Opens enemy movement control terminal (press ENTER to start)

#### Topic Namespace Behavior
**Important Note**: PX4 uses different namespacing for each instance:
- **Instance 0 (ally)**: No namespace prefix (e.g., `/fmu/in/offboard_control_mode`, `/fmu/out/vehicle_status_v1`)
  - This maintains backward compatibility with single-drone code
- **Instance 1 (enemy)**: All topics under `/px4_1/` namespace (e.g., `/px4_1/fmu/in/offboard_control_mode`)

When writing ROS2 nodes:
- For **ally drone (instance 0)**: Use topics without namespace like `/fmu/in/trajectory_setpoint`
- For **enemy drone (instance 1)**: Use namespaced topics like `/px4_1/fmu/in/trajectory_setpoint`

**IMPORTANT: Manual Enemy Drone Setup**
After the enemy drone PX4 console appears (Terminal 3), you MUST manually run:
```
commander arm -f
commander takeoff
```
This arms and launches the enemy drone. Only after these commands succeed, go to the Enemy Movement terminal (Terminal 6) where you'll see a menu:
- Press `1` for circular movement
- Press `2` for figure-8 movement
- Press `3` for random movement
- Enter duration in seconds (or press ENTER for infinite)
- Any other key defaults to circular movement with infinite duration

### Monitor System

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
- **Output**: 2D pixel coordinates

### Tracking Module (`halcon1_tracking`)
- **Current**: Simple 2D→3D conversion
- **Output**: 3D position + velocity

### Prediction Module (`halcon1_guidance`)
- **Current**: Generates instantaneous target acceleration for PX4
- **Output**: Trajectory Setpoint (acceleration) at 50 Hz

## Data Flow

```
Camera (simulated) → /enemy/detection (x,y pixels)
                  ↓
                  → /enemy/tracked (x,y,z meters)
                  ↓
                  → /interception/command (target)
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

If you are running the Gazebo simulation, you can also visualize in real time ros2 topics: with everything up and running, 
call `ros2 run rviz2 rviz2`. This opens the `RViz` GUI. Select `add` button, then select the `by topic` tab. There you will 
be able to see visualizable ros2 topics in real time (`/enemy/pose`, `/enemy/predicted_trajectory`, `/debug/interception_trajectory`).

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