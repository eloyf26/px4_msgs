# Gazebo Harmonic Simulation

## Overview

Gazebo Harmonic is the **default** simulator for Halcon1. It's fast, lightweight, and perfect for development and testing.

**Key Features:**
- ⚡ **Fast simulation** - Runs faster than real-time on most hardware
- 🖥️ **Headless mode** - Can run without GUI for CI/CD
- 🔧 **Easy debugging** - Simple physics, predictable behavior
- 📦 **Small footprint** - ~500MB disk space
- ✅ **Stable** - Mature, well-tested simulator

## Installation

### Prerequisites

- Ubuntu 22.04 (recommended)
- ROS2 Humble
- ~500MB disk space

### Install Gazebo Harmonic

```bash
# Add OSRF repository
sudo apt-get update
sudo apt-get install lsb-release wget gnupg

sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

# Install Gazebo Harmonic
sudo apt-get update
sudo apt-get install gz-harmonic

# Verify installation
gz sim --version
# Should show: Gazebo Sim, version 8.x.x
```

### Build Halcon1 for Gazebo

```bash
cd /path/to/halcon1-system
./setup.sh --gazebo
```

This will:
- Build PX4 SITL with Gazebo support
- Build `ros_gz_bridge` from source (for ROS2 Humble compatibility)
- Build MicroXRCE-DDS Agent
- Build all Halcon1 ROS2 packages

## Usage

### Quick Start (Single Drone)

```bash
# Launch Gazebo simulation
./scripts/launch_unified.sh --sim gazebo

# Or with debug mode (RViz2)
./scripts/launch_unified.sh --sim gazebo --debug
```

This starts:
1. Gazebo with X500 quadcopter + camera
2. PX4 SITL (Software-In-The-Loop)
3. MicroXRCE-DDS Agent (PX4 ↔ ROS2 bridge)
4. Camera bridge (Gazebo topics → ROS2)
5. Halcon1 pipeline (detection, tracking, guidance)

### Multi-Drone Setup

```bash
# Launch with ally and enemy drones
./scripts/launch_unified.sh --sim gazebo --mode multi
```

**Manual Enemy Control:**
After enemy drone takes off, you can control it with:
```bash
# In the Enemy Control terminal that opens:
# Press 1: Circular movement
# Press 2: Figure-8 pattern
# Press 3: Random movement
```

### Legacy Scripts (Still Available)

If you prefer the old multi-terminal approach:
```bash
# Terminal 1: PX4 SITL
./simulation/gazebo/launch/launch_px4_offboard.sh

# Terminal 2: MicroXRCE Agent
./scripts/launch_agent.sh

# Terminal 3: Camera Bridge
./scripts/launch_camera_bridge.sh

# Terminal 4: Halcon1 Pipeline
./scripts/launch_halcon1.sh
```

## Configuration

### World Selection

```bash
# Use default world
./scripts/launch_unified.sh --sim gazebo

# Use custom world (future feature)
./scripts/launch_unified.sh --sim gazebo --world custom_city
```

**Available Worlds:**
- `default` - Empty world with flat ground plane
- Custom worlds coming soon in `simulation/gazebo/config/worlds/`

### Camera Configuration

Gazebo camera specs (matches AirSim):
- Resolution: 640×480
- Field of View: 60°
- Frame rate: 30 Hz
- Image format: RGB8

## ROS2 Topics

### Published by Gazebo/PX4

```bash
# Camera data
/camera/image              # sensor_msgs/Image (RGB camera feed)
/camera/camera_info        # sensor_msgs/CameraInfo (intrinsics)

# PX4 data (from MicroXRCE-DDS Agent)
/fmu/out/vehicle_odometry           # Vehicle position/velocity
/fmu/out/vehicle_status             # Armed state, flight mode
/fmu/out/vehicle_local_position     # Local NED position
```

### Subscribed by PX4

```bash
# Commands from Halcon1 guidance
/fmu/in/trajectory_setpoint         # Target position/velocity
/fmu/in/offboard_control_mode       # Enable offboard mode
```

## Monitoring

### View Camera Feed

```bash
ros2 run rqt_image_view rqt_image_view
# Select /camera/image topic
```

### Check Topics

```bash
# List all topics
ros2 topic list

# Check camera publishing rate
ros2 topic hz /camera/image

# Echo PX4 odometry
ros2 topic echo /fmu/out/vehicle_odometry --once
```

### RViz2 Visualization

```bash
# Launch with debug mode
./scripts/launch_unified.sh --sim gazebo --debug

# Or manually
ros2 run rviz2 rviz2
# Then add topics: /enemy/pose, /debug/interception_trajectory, etc.
```

## Troubleshooting

### "gz sim" Command Not Found

```bash
# Check if Gazebo is installed
which gz

# If not found, install
sudo apt-get install gz-harmonic
```

### Camera Bridge Not Working

**Symptom**: `ros2 topic list` shows no `/camera/image`

**Solution**:
```bash
# Check Gazebo is publishing
gz topic --list | grep camera
# Should show /camera/image and /camera/camera_info

# Check ros_gz_bridge is running
ps aux | grep ros_gz_bridge

# Rebuild ros_gz from source
cd ws_ros2
colcon build --packages-select ros_gz_bridge --cmake-clean-cache
```

### PX4 Fails to Connect to Gazebo

**Symptom**: PX4 log shows "Failed to connect to gazebo"

**Solution**:
```bash
# Make sure Gazebo is running first
gz sim --version

# Check PX4 environment variables
echo $PX4_GZ_SIM_RENDER_ENGINE  # Should be ogre2

# Clean PX4 build
cd external/PX4-Autopilot
make clean
make px4_sitl gz_x500_mono_cam
```

### Simulation is Slow

**Options**:
1. **Disable GUI**: Edit launch script to add `--headless` flag
2. **Lower physics rate**: Reduce real-time factor
3. **Software rendering**: Already enabled for WSL2

```bash
# Check if running in headless mode
ps aux | grep "gz sim" | grep headless
```

## Performance

Typical performance on modern hardware:

| Hardware | Real-Time Factor | Frame Rate |
|----------|------------------|------------|
| CPU: Intel i5-11th gen, GPU: Integrated | 1.0x | 30 FPS |
| CPU: Intel i7-12th gen, GPU: NVIDIA RTX 3060 | 1.5x | 60 FPS |
| CPU: AMD Ryzen 9, GPU: NVIDIA RTX 4080 | 2.0x | 90+ FPS |

**Real-Time Factor > 1.0**: Simulation runs faster than real-time (good for testing!)

## Advanced Features

### Headless Mode (No GUI)

```bash
# Edit simulation/gazebo/engine.py
# Add to launch_simulator():
gz_cmd = ["gz", "sim", "--headless", "default.sdf"]
```

### Record Simulation

```bash
# Launch with recording enabled
./scripts/launch_unified.sh --sim gazebo --record

# Replay with rosbag
ros2 bag play <bag_file>
```

### Custom Drone Models

1. Create SDF model in `simulation/gazebo/config/models/`
2. Set environment variable:
   ```bash
   export PX4_SIM_MODEL=my_custom_model
   ```

## See Also

- [PX4 + Gazebo Documentation](https://docs.px4.io/main/en/sim_gazebo_gz/)
- [Gazebo Tutorials](https://gazebosim.org/docs)
- [Main Simulation Docs](../common/README.md)
