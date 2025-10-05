# AirSim Simulation

## Overview

Microsoft AirSim provides **photo-realistic** simulation using Unreal Engine. It's ideal for computer vision research, realistic testing, and creating demo videos.

**Key Features:**
- 🎨 **Photo-realistic rendering** - Unreal Engine 4/5 graphics
- 📸 **Advanced cameras** - RGB, depth, segmentation
- 🌤️ **Weather effects** - Rain, fog, time of day
- 🎮 **Pre-built environments** - Download ready-to-use worlds
- 🔬 **Computer vision research** - Better for CV algorithm development

**⚠️ Note**: AirSim requires native Linux (no WSL2) and NVIDIA/AMD GPU with Vulkan support.

## Installation

### Prerequisites

- **Ubuntu 22.04** (native installation, NOT WSL2)
- **GPU**: NVIDIA or AMD with Vulkan drivers
- **Disk Space**: 2-8GB (depending on environment)
- **RAM**: 8GB minimum, 16GB recommended
- **ROS2 Humble**: Already installed

### Step 1: Install AirSim Python Packages

```bash
pip install airsim msgpack-rpc-python
```

### Step 2: Build Halcon1 for AirSim

```bash
cd /path/to/halcon1-system
./setup.sh --airsim
```

This will:
- Install AirSim Python dependencies
- Build `camera_bridge` ROS2 package
- Build `viz_translator` for RViz2
- Copy `settings.json` to `~/Documents/AirSim/`
- Validate configuration

### Step 3: Download AirSim Environment

Choose one environment:

**Option A: Blocks (Recommended for Testing)**
```bash
./scripts/install_airsim_env.sh --blocks
```
- Size: ~400MB
- Best for: Quick testing, development
- Fast loading, simple environment

**Option B: Landscape Mountains (Realistic)**
```bash
./scripts/install_airsim_env.sh --landscape
```
- Size: ~5GB
- Best for: Realistic outdoor scenarios
- Beautiful terrain, more demanding

**Option C: City Environment (Urban)**
```bash
./scripts/install_airsim_env.sh --city
```
- Size: ~8GB
- Best for: Urban interception scenarios
- Buildings, streets, complex environment

### Step 4: Verify Installation

```bash
./scripts/launch_unified.sh --sim airsim --validate
```

## Usage

### Quick Start (Single Drone)

**Terminal 1: Launch AirSim Environment**
```bash
cd ~/AirSimEnvironments/Blocks/
./Blocks.sh
# Wait for Unreal Engine to load fully
```

**Terminal 2: Launch Halcon1**
```bash
cd /path/to/halcon1-system
./scripts/launch_unified.sh --sim airsim
```

This starts:
1. PX4 SITL (connects to AirSim via TCP port 4560)
2. MicroXRCE-DDS Agent (PX4 ↔ ROS2)
3. AirSim Camera Bridge (publishes `/camera/image`)
4. Halcon1 pipeline (detection, tracking, guidance)

**With Debug Mode:**
```bash
./scripts/launch_unified.sh --sim airsim --debug
# Launches RViz2 + visualization translator
```

### Multi-Drone Setup (Ally vs Enemy)

**Terminal 1: Launch AirSim**
```bash
cd ~/AirSimEnvironments/Blocks/
./Blocks.sh
# You should see BOTH drones spawn
```

**Terminal 2: Launch Halcon1 Multi-Drone**
```bash
./scripts/launch_unified.sh --sim airsim --mode multi
```

**Manual Enemy Control:**
The system will launch a Python script that lets you control the enemy drone:
- Press `1`: Circular movement pattern
- Press `2`: Figure-8 pattern
- Press `3`: Random movement

### Legacy Launch (Old Method)

If you prefer the original multi-terminal approach:
```bash
# Launch manually (from old scripts)
./simulation/airsim/launch/launch_airsim.sh --multi --debug
```

## Configuration

### AirSim Settings File

Location: `~/Documents/AirSim/settings.json`

**Key Parameters:**

```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",
  "ClockType": "SteppableClock",  // LockStep mode for PX4

  "Vehicles": {
    "Ally": {
      "VehicleType": "PX4Multirotor",
      "LockStep": true,
      "UseTcp": true,
      "TcpPort": 4560,
      "Cameras": {
        "front_center": {
          "CaptureSettings": [{
            "ImageType": 0,  // RGB
            "Width": 640,
            "Height": 480,
            "FOV_Degrees": 60
          }]
        }
      }
    }
  }
}
```

**Configuration Files in Repo:**
- `simulation/airsim/config/settings.json` - Single drone
- `simulation/airsim/config/settings_multi.json` - Ally + Enemy (future)

### Camera Configuration

AirSim camera specs (matches Gazebo):
- Resolution: 640×480
- Field of View: 60°
- Frame rate: 30 Hz
- Image type: Scene (RGB)

To change camera parameters, edit `settings.json` and restart AirSim.

## AirSim Controls

### Camera Views

| Key | Function |
|-----|----------|
| `\` (Backslash) | **Cycle between vehicles** (Ally → Enemy → Ally) |
| `0-9` | Switch camera angles for current vehicle |
| `0` | Default chase camera (follows behind drone) |
| `1` | Front camera view (FPV) |
| `/` | Toggle sub-window (Ally's front camera) |

### Camera Movement (Observer Mode)

| Keys | Function |
|------|----------|
| `W/A/S/D` | Move camera forward/left/backward/right |
| `Q/E` | Move camera down/up |
| Mouse + Right-click | Look around |
| Mouse Scroll | Zoom in/out |

### Recording & Display

| Key | Function |
|-----|----------|
| `R` | Start/stop recording (saved to Documents/AirSim/) |
| `PrtScn` | Take screenshot |
| `F1` | Toggle help menu |
| `T` | Toggle trajectory trace lines |
| `;` | Pause/unpause simulation |

### Performance Tuning

Open Unreal console with `~` (tilde) and type:

```
r.ScreenPercentage 70      # Lower rendering resolution (better FPS)
sg.ViewDistanceScale 0.5   # Reduce view distance
stat fps                   # Show FPS counter
```

## ROS2 Topics

### Published by AirSim Bridges

```bash
# Camera data (from camera_bridge)
/camera/image              # sensor_msgs/Image (RGB camera feed)
/camera/camera_info        # sensor_msgs/CameraInfo (intrinsics)

# PX4 data (from MicroXRCE-DDS Agent)
/fmu/out/vehicle_odometry           # Vehicle position/velocity
/fmu/out/vehicle_status             # Armed state, flight mode

# Visualization (from viz_translator, debug mode only)
/ally/pose                          # PoseStamped for RViz2
/ally/path                          # Path history
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

### Check Camera Bridge Status

```bash
# Check if bridge is running
ros2 node list | grep airsim

# Check camera topics
ros2 topic list | grep camera

# Check camera frame rate
ros2 topic hz /camera/image
# Should show ~30 Hz
```

### RViz2 Visualization

```bash
# Already launched in debug mode
./scripts/launch_unified.sh --sim airsim --debug

# Add topics in RViz2:
# - /ally/pose (PoseStamped)
# - /ally/path (Path)
# - /debug/interception_trajectory (Path)
```

## Troubleshooting

### AirSim Won't Start

**Symptom**: Unreal Engine crashes or fails to load

**Solutions**:
1. Check Vulkan support:
   ```bash
   vulkaninfo | head -20
   ```
2. Update GPU drivers
3. Try different environment (Blocks is most stable)
4. Check system resources (close other apps)

### "Cannot Connect to AirSim" Error

**Symptom**: `camera_bridge` fails with connection error

**Solutions**:
1. Ensure AirSim is fully loaded (you see the drone in the scene)
2. Check `settings.json` is in `~/Documents/AirSim/`
3. Verify AirSim is listening on API port:
   ```bash
   netstat -an | grep 41451
   # Should show LISTENING on port 41451
   ```
4. Try restarting AirSim

### PX4 Won't Connect to AirSim

**Symptom**: PX4 log shows "Waiting for TCP connection on port 4560"

**Solutions**:
1. Check `settings.json` has:
   ```json
   "UseTcp": true,
   "TcpPort": 4560,
   "LockStep": true
   ```
2. Ensure AirSim is running BEFORE starting PX4
3. Check no firewall blocking port 4560:
   ```bash
   sudo netstat -tulpn | grep 4560
   ```

### Camera Feed is Black/Frozen

**Solutions**:
1. Press `\` to ensure you're viewing the Ally drone
2. Check camera is enabled in settings.json
3. Restart both AirSim and the camera bridge
4. Verify in AirSim that camera view works (press `1` for FPV)

### Low Frame Rate / Laggy Simulation

**Solutions**:
1. Lower rendering quality (see Performance Tuning above)
2. Close other applications
3. Use Blocks environment (lighter than City/Landscape)
4. Disable recording if enabled
5. Ensure GPU drivers are up-to-date

### WSL2 Issues

**Important**: AirSim does NOT support WSL2 due to Vulkan limitations.

**Solution**: Use native Ubuntu installation or dual-boot.

## Performance

Typical performance on different hardware:

| Hardware | FPS | Settings |
|----------|-----|----------|
| RTX 3060, i5-11th gen | 45-60 | High quality |
| RTX 4070, i7-12th gen | 60-90 | High quality |
| RTX 4090, Ryzen 9 | 100+ | Ultra quality |
| GTX 1660, i5-10th gen | 25-35 | Medium quality |

**Tips for Better Performance:**
- Use Blocks environment (lightest)
- Lower screen percentage to 70%
- Reduce view distance
- Close background applications

## Advanced Features

### Recording Flight Data

AirSim automatically records when you press `R`:
- **Location**: `~/Documents/AirSim/<timestamp>/`
- **Contents**: Images, camera poses, IMU data

### Capture High-Quality Images

```python
import airsim

client = airsim.MultirotorClient()
client.confirmConnection()

# Get high-res image
responses = client.simGetImages([
    airsim.ImageRequest("front_center", airsim.ImageType.Scene, False, False)
])

# Save to file
import cv2
img = airsim.string_to_uint8_array(responses[0].image_data_uint8)
cv2.imwrite("capture.png", img)
```

### Weather and Time of Day

Edit `settings.json`:

```json
"TimeOfDay": {
  "Enabled": true,
  "StartDateTime": "2023-06-15 12:00:00",
  "CelestialClockSpeed": 1.0
},
"Weather": {
  "Rain": 0.5,      // 0.0 to 1.0
  "Roadwetness": 0.5,
  "Snow": 0.0,
  "RoadSnow": 0.0,
  "MapleLeaf": 0.0,
  "RoadLeaf": 0.0,
  "Dust": 0.0,
  "Fog": 0.3
}
```

### Depth Camera

Add depth camera to `settings.json`:

```json
"Cameras": {
  "front_center": {
    "CaptureSettings": [
      {
        "ImageType": 0,  // RGB
        "Width": 640,
        "Height": 480,
        "FOV_Degrees": 60
      },
      {
        "ImageType": 2,  // DepthPlanar
        "Width": 640,
        "Height": 480,
        "FOV_Degrees": 60
      }
    ]
  }
}
```

Then modify `camera_bridge` to publish depth.

## See Also

- [AirSim Official Docs](https://microsoft.github.io/AirSim/)
- [PX4 + AirSim Integration](https://docs.px4.io/main/en/sim_airsim/)
- [Main Simulation Docs](../common/README.md)
- [Gazebo Comparison](../gazebo/README.md)
