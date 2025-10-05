# AirSim Quick Start Guide

Get the Halcon1 system running with **AirSim + Unreal Engine** in just 3 steps (~10 minutes).

## Why AirSim?

- ✅ **Photo-realistic graphics** powered by Unreal Engine
- ✅ **Same Halcon1 code** - detection, tracking, guidance work unchanged
- ✅ **Same PX4 flight controller** - identical to Gazebo and real hardware
- ✅ **Pre-built environments** - no compilation needed
- ✅ **Better camera simulation** - realistic lighting, shadows, reflections

## Prerequisites

**System Requirements:**
- Ubuntu 22.04 (native installation, **not WSL2**)
- GPU with Vulkan support (NVIDIA/AMD)
- ROS2 Humble installed
- ~2-8GB disk space (depending on environment)

**Why not WSL2?** AirSim requires Vulkan drivers which are not fully supported in WSL2.

## Installation (3 Steps)

### Step 1: Setup Halcon1 for AirSim (~2 minutes)

```bash
cd /home/eloy/Documents/Projects/drone-ws/halcon1-system

# Install AirSim dependencies and build bridge
./setup.sh --airsim
```

This automatically:
- ✅ Installs AirSim Python packages (airsim, msgpack-rpc-python)
- ✅ Builds `airsim_camera_bridge` ROS2 package
- ✅ Builds `airsim_viz_translator` for RViz2 visualization
- ✅ Copies settings.json to `~/Documents/AirSim/`
- ✅ Validates configuration

### Step 2: Download AirSim Environment (~3 minutes)

Choose one environment to download:

**Option A: Blocks (Recommended for testing)**
```bash
./scripts/install_airsim_env.sh --blocks
```
- Size: ~400MB
- Best for: Quick testing, development
- Location: `~/AirSimEnvironments/Blocks/`

**Option B: Landscape Mountains (Realistic outdoor)**
```bash
./scripts/install_airsim_env.sh --landscape
```
- Size: ~5GB
- Best for: Realistic outdoor scenarios
- Location: `~/AirSimEnvironments/LandscapeMountains/`

**Option C: City Environment (Urban scenarios)**
```bash
./scripts/install_airsim_env.sh --city
```
- Size: ~8GB
- Best for: Urban testing, buildings
- Location: `~/AirSimEnvironments/CityEnviron/`

**Custom install directory:**
```bash
./scripts/install_airsim_env.sh --blocks --dir /path/to/custom/location
```

### Step 3: Validate Setup (~1 minute)

```bash
./scripts/validate_setup.sh
```

You should see:
- ✅ AirSim Python packages: Installed
- ✅ airsim_camera_bridge: Built
- ✅ AirSim settings.json: Present
- ✅ AirSim environment: Downloaded

## Running the System

### Launch AirSim Simulation

**Terminal 1: Start AirSim Environment**
```bash
# Navigate to your chosen environment
cd ~/AirSimEnvironments/Blocks/

# Launch Unreal Engine
./Blocks.sh
```

**Wait for:**
- Unreal Engine to load (~30 seconds first time)
- "Waiting for connection..." message in AirSim window

**Terminal 2: Launch Halcon1 System**
```bash
cd /home/eloy/Documents/Projects/drone-ws/halcon1-system

# Normal mode (3 terminals: Agent + PX4 + Camera)
./scripts/launch_airsim.sh

# Debug mode (5 terminals: Agent + PX4 + Camera + Translator + RViz2)
./scripts/launch_airsim.sh --debug
```

This automatically launches:
- 🔹 **MicroXRCE Agent** - PX4 ↔ ROS2 bridge (UDP 8888)
- 🔹 **PX4 SITL** - Flight controller (connects to AirSim TCP 4560)
- 🔹 **AirSim Camera Bridge** - Publishes `/camera/image` at 30 Hz

**Debug mode additionally launches:**
- 🔹 **PX4 Debug Translator** - Converts `/fmu/*` to RViz-friendly topics
- 🔹 **RViz2** - 3D visualization of drone pose, trajectory, velocity

### Control the Drone

**Option A: QGroundControl (Recommended)**
```bash
# QGC should auto-connect to PX4 on UDP 14550
# Use QGC interface to:
# 1. Arm the drone
# 2. Takeoff
# 3. Mission planning
```

**Option B: PX4 Console Commands**

In the PX4 SITL terminal:
```bash
pxh> commander arm
pxh> commander takeoff
```

### Verify Camera Feed

```bash
# Check topics exist
ros2 topic list | grep camera
# Should show:
# /camera/image
# /camera/camera_info

# Check publishing rate
ros2 topic hz /camera/image
# Should show: ~30 Hz

# Visualize camera
ros2 run rqt_image_view rqt_image_view
# Select /camera/image from dropdown
```

### Monitor Drone State (Debug Mode)

If launched with `--debug` flag, check RViz2 visualization topics:

```bash
ros2 topic list | grep debug
```

Available debug topics:
- `/debug/ally/pose` - Drone position (PoseStamped)
- `/debug/ally/path` - Flight trajectory (Path)
- `/debug/ally/odometry` - Full state (Odometry)
- `/debug/ally/velocity` - Velocity vector (TwistStamped)
- `/debug/ally/setpoint` - Desired position (PoseStamped)
- `/debug/ally/status` - Flight mode (String)
- `/debug/ally/nav_state` - Navigation state (Int32)

## Running Halcon1 Pipeline

Once the drone is flying and camera is working:

```bash
# Terminal 3: Start detection, tracking, guidance nodes
./scripts/launch_halcon1.sh
```

This launches:
- 🎯 **halcon1_detection** - YOLOv11n drone detection
- 📍 **halcon1_tracking** - Camera-to-world coordinate transform
- 🎮 **halcon1_guidance** - Kalman Filter + Proportional Navigation

Monitor the pipeline:
```bash
ros2 topic echo /enemy/detection --once    # 2D detections
ros2 topic echo /enemy/tracked --once      # 3D world coordinates
ros2 topic echo /interception/command --once  # Guidance commands
```

## Switching Environments

To try a different environment:

1. Close current AirSim window (Ctrl+C or close window)
2. Navigate to new environment:
   ```bash
   cd ~/AirSimEnvironments/LandscapeMountains/
   ./LandscapeMountains.sh
   ```
3. Re-run `./scripts/launch_airsim.sh` (no need to rebuild)

**Note:** All environments use the same `~/Documents/AirSim/settings.json`

## Cleanup

To stop all processes:

```bash
# Kill AirSim environment (in AirSim terminal)
Ctrl+C

# Kill Halcon1 terminals
# In each terminal: Ctrl+C

# Or use cleanup script for PX4/ROS2 processes
./scripts/cleanup_airsim.sh  # If available
# Or manually:
pkill -9 px4
pkill -9 MicroXRCEAgent
```

## Troubleshooting

### AirSim won't start
```bash
# Check Vulkan support
vulkaninfo | grep "Vulkan Instance"

# If missing, install Vulkan:
sudo apt install libvulkan1 vulkan-utils
```

### PX4 can't connect to AirSim
```bash
# Check settings.json has TCP enabled
cat ~/Documents/AirSim/settings.json | grep -A2 TcpPort
# Should show:
#   "UseTcp": true,
#   "TcpPort": 4560,

# Verify AirSim is running and waiting for connection
# Check AirSim window shows "Waiting for connection..."
```

### Camera bridge not publishing
```bash
# Check AirSim Python package
python3 -c "import airsim; print('OK')"

# Rebuild camera bridge
cd /home/eloy/Documents/Projects/drone-ws/halcon1-system/ws_ros2
colcon build --packages-select airsim_camera_bridge
source install/setup.bash

# Check AirSim camera exists
python3 << EOF
import airsim
client = airsim.MultirotorClient()
client.confirmConnection()
cameras = client.simListSceneObjects(".*[Cc]amera.*")
print(f"Available cameras: {cameras}")
EOF
```

### RViz2 shows no data (Debug mode)
```bash
# Check translator is running
ros2 node list | grep px4_debug_translator

# Verify /fmu topics exist
ros2 topic list | grep /fmu/out

# Rebuild viz translator
cd /home/eloy/Documents/Projects/drone-ws/halcon1-system/ws_ros2
colcon build --packages-select airsim_viz_translator
source install/setup.bash
```

### Settings.json not found
```bash
# Manually copy settings
mkdir -p ~/Documents/AirSim
cp config/airsim/settings.json ~/Documents/AirSim/

# Verify
cat ~/Documents/AirSim/settings.json
```

### Performance issues (low FPS)
```bash
# Lower AirSim graphics quality:
# In AirSim window:
# - Press ~ (tilde) to open console
# - Type: sg.ViewDistanceScale 0.5
# - Type: r.ScreenPercentage 70

# Or edit settings.json:
# Add under "SimMode":
#   "ViewMode": "NoDisplay"  # Runs headless (no graphics)
```

## AirSim vs Gazebo Comparison

| Feature | Gazebo | AirSim |
|---------|--------|--------|
| **Setup Time** | ~5 min | ~10 min |
| **Disk Space** | ~500MB | ~2-8GB |
| **Graphics** | Ogre2 | Unreal Engine |
| **Physics** | ODE/Bullet | PhysX (NVIDIA) |
| **Camera Quality** | Good | Photo-realistic |
| **Performance** | Fast | Moderate (GPU) |
| **Custom Environments** | SDF files | Unreal Editor |
| **Halcon1 Code Changes** | ✅ None | ✅ None |
| **PX4 Code** | ✅ Same | ✅ Same |

## Next Steps

- 📖 **Detailed Settings**: [config/airsim/README.md](../config/airsim/README.md)
- 🧪 **Testing Guide**: [TESTING.md](../TESTING.md)
- 🏗️ **System Architecture**: [README.md](../README.md#system-architecture)
- 📋 **Implementation Details**: [AIRSIM_IMPLEMENTATION_PLAN.md](../AIRSIM_IMPLEMENTATION_PLAN.md)

## Additional Resources

- [AirSim Official Documentation](https://microsoft.github.io/AirSim/)
- [AirSim Settings Reference](https://microsoft.github.io/AirSim/settings/)
- [PX4 AirSim Setup Guide](https://microsoft.github.io/AirSim/px4_setup/)
- [Halcon1 Main README](../README.md)

---

**Questions or Issues?** Check [config/airsim/README.md](../config/airsim/README.md) for advanced troubleshooting.
