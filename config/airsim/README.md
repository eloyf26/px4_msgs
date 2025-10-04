# AirSim Configuration for Halcon1

## Overview

This directory contains the AirSim configuration file for running Halcon1 system with AirSim + Unreal Engine simulation.

## AirSim Keyboard Controls & Camera Views

### Camera Views
- **`\` (Backslash)**: Cycle between vehicles (Ally → Enemy → Ally)
- **`0-9` (Number keys)**: Switch between camera angles for current vehicle
  - `0`: Default chase camera (follows behind drone)
  - `1`: Front camera view (FPV - First Person View)
  - `2`: Ground observer view
  - Other numbers: Additional camera positions
- **`/` (Forward slash)**: Toggle sub-window display (Ally's front camera)

### Camera Movement (Manual/Observer Mode)
- **`W/A/S/D`**: Move camera forward/left/backward/right
- **`Q/E`**: Move camera down/up
- **Mouse**: Look around (hold right-click and drag)
- **Mouse Scroll**: Zoom in/out

### Recording & Capture
- **`R`**: Start/stop recording (saves to Documents/AirSim/)
- **`PrtScn` (Print Screen)**: Take screenshot

### Display Options
- **`F1`**: Toggle help menu (shows all keyboard shortcuts)
- **`F5`**: Toggle API control indicators
- **`T`**: Toggle trace lines (shows vehicle trajectory)
- **`~` (Tilde)**: Open Unreal Engine console
  - Type `r.ScreenPercentage 70` - Lower graphics quality
  - Type `sg.ViewDistanceScale 0.5` - Reduce view distance
  - Type `stat fps` - Show FPS counter

### Simulation Control
- **`;` (Semicolon)**: Pause/unpause simulation
- **`Alt + F4`**: Quit AirSim

### Multi-Drone Specific
When running with `--multi` flag (Ally + Enemy):
- Press `\` to see Enemy drone location
- Enemy drone is controlled via Python script (not keyboard)
- Ally drone is controlled by PX4 (via QGroundControl or offboard commands)

### Important Notes
- **You cannot manually control PX4Multirotor (Ally)** with keyboard - it's controlled by PX4 autopilot
- **Enemy (SimpleFlight)** is controlled via AirSim Python API (control_enemy_airsim.py)
- Camera controls only affect your view, not the drone's flight

## Quick Setup (Automated)

The easiest way to configure AirSim for Halcon1:

```bash
# From halcon1-system root directory
./setup.sh --airsim
```

This automatically:
- ✅ Copies `settings.json` to `~/Documents/AirSim/`
- ✅ Creates backup of existing settings (if any)
- ✅ Validates JSON syntax
- ✅ Installs AirSim Python dependencies
- ✅ Builds airsim_camera_bridge and airsim_viz_translator packages

## Manual Setup

If you prefer manual setup or need to customize:

### 1. Copy settings.json to AirSim Config Directory

AirSim reads its configuration from a specific directory:

**Linux:**
```bash
mkdir -p ~/Documents/AirSim
cp config/airsim/settings.json ~/Documents/AirSim/
```

**Windows:**
```powershell
mkdir $env:USERPROFILE\Documents\AirSim
copy config\airsim\settings.json $env:USERPROFILE\Documents\AirSim\
```

**Note**: WSL2 is not supported for running AirSim (Vulkan driver limitations). Use native Linux installation.

### 2. Verify Configuration

After copying, the file should be located at:
- Linux: `~/Documents/AirSim/settings.json`
- Windows: `C:\Users\<YourUsername>\Documents\AirSim\settings.json`

Verify the configuration:
```bash
# Check file exists
ls -lh ~/Documents/AirSim/settings.json

# Validate JSON syntax
python3 -c "import json; json.load(open('$HOME/Documents/AirSim/settings.json'))" && echo "✅ Valid JSON"

# Check critical settings
cat ~/Documents/AirSim/settings.json | grep -E "PX4Multirotor|TcpPort|LockStep"
```

## Configuration Details

### Global Settings

- **SettingsVersion**: `1.2` - AirSim settings format version
- **SimMode**: `"Multirotor"` - Enables multirotor simulation mode
- **ClockType**: `"SteppableClock"` - Required for LockStep mode with PX4
- **ViewMode**: `"SpringArmChase"` - Third-person camera following the drone
- **LocalHostIp**: `"127.0.0.1"` - IP address for local connections
- **RecordUIVisible**: `false` - Hides recording UI overlay
- **LogMessagesVisible**: `true` - Shows AirSim log messages

### Vehicle: "Ally" (PX4Multirotor)

This is the drone controlled by PX4 SITL and your Halcon1 ROS2 nodes.

**Vehicle Settings:**
- **VehicleType**: `"PX4Multirotor"` - Uses PX4 flight controller (not SimpleFlight)
- **UseSerial**: `false` - Disable serial communication
- **UseTcp**: `true` - MAVLink communication over TCP
- **TcpPort**: `4560` - PX4 connects to this port
- **ControlIp**: `"127.0.0.1"` - IP address for PX4 connection
- **LockStep**: `true` - **Critical!** Synchronizes physics with PX4 time for deterministic simulation

**Spawn Position** (NED coordinates):
- **X**: `0` - North/South position (meters)
- **Y**: `0` - East/West position (meters)
- **Z**: `0` - Down position (meters, 0 = ground level)
- **Pitch/Roll/Yaw**: `0` - Initial orientation (degrees)

**Sensors** (all enabled for PX4):
- **Imu** (SensorType 2): Inertial Measurement Unit
- **Gps** (SensorType 3): Global Positioning System
- **Magnetometer** (SensorType 4): Compass/heading sensor
- **Barometer** (SensorType 1): Altitude/pressure sensor

## Camera Configuration

The `front_center` camera is mounted on the "Ally" drone:

**Camera Settings:**
- **Name**: `front_center`
- **ImageType**: `0` - Scene/RGB image (0=Scene, 1=DepthPlanner, 2=DepthPerspective, 5=Segmentation)
- **Width**: `640` pixels
- **Height**: `480` pixels
- **FOV_Degrees**: `60` - Field of view (matches Gazebo configuration)
- **AutoExposureSpeed**: `100` - Camera exposure adjustment speed
- **AutoExposureMaxBrightness**: `0.64` - Maximum brightness target
- **AutoExposureMinBrightness**: `0.03` - Minimum brightness target
- **MotionBlurAmount**: `0` - Disabled for clear images
- **TargetGamma**: `1.0` - Gamma correction (1.0 = linear)

**Camera Position** (relative to drone center):
- **X**: `0.3` meters forward
- **Y**: `0.0` meters (centered)
- **Z**: `0.0` meters (drone level)
- **Pitch/Roll/Yaw**: `0°` - Facing straight forward

This configuration ensures camera images from AirSim match Gazebo for YOLO detection compatibility.

## ROS2 Topic Mapping

When using `airsim_camera_bridge` (Python-based bridge), the following topics are published:

**Published Topics:**
- `/camera/image` - RGB camera images (sensor_msgs/Image)
- `/camera/camera_info` - Camera intrinsic parameters (sensor_msgs/CameraInfo)

These topics are identical to Gazebo, allowing Halcon1 detection/tracking nodes to work unchanged.

## LockStep Mode

**What is LockStep?**
- Synchronizes AirSim physics simulation with PX4 time
- PX4 sends a "step" command → AirSim advances physics by one tick → repeat
- Ensures perfect time synchronization between flight controller and physics
- Critical for accurate control and sensor simulation

**Without LockStep:**
- Physics runs at real-time or faster
- PX4 may miss sensor updates or send delayed commands
- Unstable flight behavior

**With LockStep (enabled in this config):**
- PX4 controls simulation time
- Deterministic, reproducible simulations
- Stable flight behavior

## Modifying the Configuration

### Add More Drones (Multi-Drone Support)

To add additional drones (e.g., enemy targets), add new vehicles to the `Vehicles` section:

```json
"Vehicles": {
  "Ally": {
    "VehicleType": "PX4Multirotor",
    ...
  },
  "Enemy": {
    "VehicleType": "SimpleFlight",
    "X": 5, "Y": 0, "Z": 0
  },
  "Enemy2": {
    "VehicleType": "SimpleFlight",
    "X": -5, "Y": 5, "Z": 0
  }
}
```

**Note**: Multi-drone support requires additional control scripts for enemy drones using the AirSim Python API.

### Change Spawn Positions

Modify the `X`, `Y`, `Z` coordinates:
- **X**: Forward (positive) / Backward (negative)
- **Y**: Right (positive) / Left (negative)
- **Z**: Down (positive) / Up (negative)

**Note**: AirSim uses NED (North-East-Down) coordinate system, different from ROS2 ENU (East-North-Up). Coordinate transformation is handled by the tracking module.

### Change Camera Settings

Modify the camera parameters under `"Ally" → "Cameras" → "front_center" → "CaptureSettings"`:

```json
{
  "ImageType": 0,        // 0=Scene, 1=DepthPlanner, 2=DepthPerspective, 5=Segmentation
  "Width": 640,
  "Height": 480,
  "FOV_Degrees": 60,
  "AutoExposureSpeed": 100,
  "MotionBlurAmount": 0
}
```

**Warning**: Changing resolution or FOV requires updating camera intrinsics in the tracking module for accurate coordinate transformation.

## Troubleshooting

### AirSim Won't Start

**Symptoms**: AirSim binary crashes or shows black screen

**Solutions**:
1. Check Vulkan support:
   ```bash
   vulkaninfo | grep "Vulkan Instance"
   ```
   If missing:
   ```bash
   sudo apt install libvulkan1 vulkan-utils
   ```

2. Check GPU drivers:
   ```bash
   # NVIDIA
   nvidia-smi

   # AMD
   lspci | grep VGA
   ```

3. First launch takes longer (~2 minutes) - be patient

4. Try running with logs:
   ```bash
   ./Blocks.sh -log 2>&1 | tee airsim.log
   ```

### PX4 Not Connecting to AirSim

**Symptoms**: PX4 console shows `Waiting for simulator...` indefinitely

**Solutions**:
1. Ensure AirSim is running and fully loaded before starting PX4
   - Look for "Waiting for connection..." message in AirSim window

2. Check that `TcpPort: 4560` matches PX4 expectations:
   ```bash
   cat ~/Documents/AirSim/settings.json | grep TcpPort
   # Should show: "TcpPort": 4560
   ```

3. Verify `LockStep: true` is set:
   ```bash
   cat ~/Documents/AirSim/settings.json | grep LockStep
   # Should show: "LockStep": true
   ```

4. Check firewall settings:
   ```bash
   sudo ufw status
   sudo ufw allow 4560/tcp
   ```

5. Test TCP connection manually:
   ```bash
   nc -zv 127.0.0.1 4560
   # Should show: Connection to 127.0.0.1 4560 port [tcp/*] succeeded!
   ```

### Camera Topics Not Appearing

**Symptoms**: `/camera/image` topic doesn't exist after starting `airsim_camera_bridge`

**Solutions**:
1. Check AirSim Python package is installed:
   ```bash
   python3 -c "import airsim; print('OK')"
   ```
   If missing:
   ```bash
   pip3 install airsim msgpack-rpc-python
   ```

2. Verify camera name matches: `front_center`
   ```bash
   cat ~/Documents/AirSim/settings.json | grep -A5 "Cameras"
   ```

3. Check vehicle name matches: `Ally`
   ```bash
   cat ~/Documents/AirSim/settings.json | grep -A2 "Vehicles"
   ```

4. Ensure AirSim is running with this settings.json:
   ```bash
   # Check AirSim loaded the file
   # Look for log message: "Reading settings from: ~/Documents/AirSim/settings.json"
   ```

5. Check ROS2 bridge is running:
   ```bash
   ros2 node list | grep airsim
   # Should show: /airsim_camera_bridge
   ```

6. Verify AirSim API connection:
   ```bash
   python3 << EOF
   import airsim
   client = airsim.MultirotorClient()
   client.confirmConnection()
   print("✅ Connected to AirSim")
   EOF
   ```

7. Check camera topics:
   ```bash
   ros2 topic list | grep camera
   # Should show:
   # /camera/image
   # /camera/camera_info
   ```

### RViz2 Not Showing Drone (Debug Mode)

**Symptoms**: RViz2 window is empty or shows errors

**Solutions**:
1. Check debug translator is running:
   ```bash
   ros2 node list | grep px4_debug_translator
   ```

2. Verify debug topics exist:
   ```bash
   ros2 topic list | grep /debug/ally
   ```

3. Check that PX4 is publishing:
   ```bash
   ros2 topic echo /fmu/out/vehicle_local_position --once
   ```

4. Rebuild viz translator if needed:
   ```bash
   cd ws_ros2
   colcon build --packages-select airsim_viz_translator
   source install/setup.bash
   ```

5. In RViz2, manually add visualizations:
   - Add → By topic → /debug/ally/pose → PoseStamped
   - Add → By topic → /debug/ally/path → Path
   - Set Fixed Frame to "map" in Global Options

### Drone Falls Immediately After Takeoff

**Symptoms**: Drone arms, takes off, then crashes

**Solutions**:
1. Ensure `LockStep: true` is enabled:
   ```bash
   cat ~/Documents/AirSim/settings.json | grep LockStep
   ```

2. Check PX4 console for sensor errors:
   ```bash
   # Look for errors like:
   # "IMU: sensor time out"
   # "GPS: no fix"
   # "MAG: sensor not found"
   ```

3. Verify all sensors are enabled (IMU, GPS, Barometer, Magnetometer):
   ```bash
   cat ~/Documents/AirSim/settings.json | grep -A10 "Sensors"
   ```

4. Try slower takeoff velocity in PX4 parameters:
   ```bash
   # In PX4 console:
   param set MPC_TKO_SPEED 1.0
   param save
   ```

5. Check AirSim physics settings:
   ```bash
   # Ensure ClockType is set correctly
   cat ~/Documents/AirSim/settings.json | grep ClockType
   # Should show: "ClockType": "SteppableClock"
   ```

### Performance Issues (Low FPS, Laggy)

**Symptoms**: AirSim runs slowly, low frame rate

**Solutions**:
1. Lower graphics quality in AirSim:
   - Press `~` (tilde) to open console
   - Type: `sg.ViewDistanceScale 0.5`
   - Type: `r.ScreenPercentage 70`

2. Reduce shadow quality:
   - Press `~` → `r.ShadowQuality 0`

3. Run headless (no graphics):
   ```json
   // In settings.json, add under "SimMode":
   "ViewMode": "NoDisplay"
   ```

4. Check GPU usage:
   ```bash
   # NVIDIA
   watch -n 1 nvidia-smi

   # Should show GPU utilization
   ```

5. Close other GPU-intensive applications

### Settings.json Not Loading

**Symptoms**: AirSim doesn't apply your custom settings

**Solutions**:
1. Check file location is correct:
   ```bash
   ls -lh ~/Documents/AirSim/settings.json
   ```

2. Validate JSON syntax:
   ```bash
   python3 -c "import json; json.load(open('$HOME/Documents/AirSim/settings.json'))" && echo "✅ Valid JSON"
   ```
   If invalid, fix JSON errors (missing commas, brackets, quotes)

3. Check AirSim logs for errors:
   ```bash
   # In AirSim window, press ~ and look for:
   # "Reading settings from: ~/Documents/AirSim/settings.json"
   ```

4. Delete cached settings:
   ```bash
   rm -rf ~/Documents/AirSim/cache/
   ```

5. Re-copy from template:
   ```bash
   cp config/airsim/settings.json ~/Documents/AirSim/
   ```

## Switching Between Environments

You can use different AirSim environments without changing this configuration file. The `settings.json` works with all AirSim environments.

**Available Environments:**

1. **Blocks** (~400MB) - Simple, fast, good for testing:
   ```bash
   ./scripts/install_airsim_env.sh --blocks
   cd ~/AirSimEnvironments/Blocks/
   ./Blocks.sh
   ```

2. **Landscape Mountains** (~5GB) - Realistic outdoor:
   ```bash
   ./scripts/install_airsim_env.sh --landscape
   cd ~/AirSimEnvironments/LandscapeMountains/
   ./LandscapeMountains.sh
   ```

3. **City Environment** (~8GB) - Urban testing:
   ```bash
   ./scripts/install_airsim_env.sh --city
   cd ~/AirSimEnvironments/CityEnviron/
   ./CityEnviron.sh
   ```

All environments share the same `~/Documents/AirSim/settings.json` configuration.

## Advanced Configuration Tips

### Running Multiple Simulations

To run multiple AirSim instances simultaneously (different machines or ports):

1. Change `TcpPort` in settings.json (e.g., 4560, 4561, 4562)
2. Start PX4 with matching simulator port:
   ```bash
   PX4_SIM_PORT_NUMBER=4561 ./scripts/launch_airsim.sh
   ```

### Recording Flight Data

Enable AirSim recording in settings.json:
```json
{
  "Recording": {
    "RecordOnMove": true,
    "RecordInterval": 0.05,
    "Cameras": ["front_center"],
    "ImageType": 0
  }
}
```

Data saved to `~/Documents/AirSim/<timestamp>/`

### Custom Weather and Time of Day

Add to settings.json:
```json
{
  "TimeOfDay": {
    "Enabled": true,
    "StartDateTime": "2023-01-01 12:00:00",
    "CelestialClockSpeed": 1
  },
  "Weather": {
    "WeatherEnabled": true,
    "WeatherParameter": 0.5  // 0=clear, 1=heavy rain/snow
  }
}
```

### Using Depth Camera for Obstacle Avoidance

Add depth camera to settings.json:
```json
"Cameras": {
  "front_center": { /* RGB camera config */ },
  "depth_camera": {
    "CaptureSettings": [
      {
        "ImageType": 2,  // DepthPerspective
        "Width": 320,
        "Height": 240,
        "FOV_Degrees": 90
      }
    ],
    "X": 0.3, "Y": 0.0, "Z": 0.0
  }
}
```

Then subscribe to depth in ROS2:
```python
# Update airsim_camera_bridge to publish depth
# Topic: /camera/depth
```

## Quick Reference

**Essential Commands:**
```bash
# Setup AirSim
./setup.sh --airsim

# Download environment
./scripts/install_airsim_env.sh --blocks

# Launch simulation
./scripts/launch_airsim.sh              # Normal mode
./scripts/launch_airsim.sh --debug      # With RViz2

# Validate setup
./scripts/validate_setup.sh

# Check settings
cat ~/Documents/AirSim/settings.json | grep -E "PX4|TcpPort|LockStep"

# Monitor topics
ros2 topic list | grep camera
ros2 topic hz /camera/image
```

**Critical Settings Checklist:**
- ✅ `VehicleType: "PX4Multirotor"` (not SimpleFlight)
- ✅ `UseTcp: true` and `TcpPort: 4560`
- ✅ `LockStep: true` (critical for stability)
- ✅ `ClockType: "SteppableClock"`
- ✅ All sensors enabled (IMU, GPS, Barometer, Magnetometer)
- ✅ Camera: 640×480, 60° FOV (matches Gazebo)

## References

- [Halcon1 AirSim Quick Start](../../docs/QUICK_START_AIRSIM.md) - Get started in 3 steps
- [AirSim Official Settings Docs](https://microsoft.github.io/AirSim/settings/)
- [PX4 AirSim Setup Guide](https://microsoft.github.io/AirSim/px4_setup/)
- [AirSim LockStep Mode](https://microsoft.github.io/AirSim/px4_sitl/)
- [AirSim Python API](https://microsoft.github.io/AirSim/apis/)
- [AirSim GitHub Releases](https://github.com/microsoft/AirSim/releases) - Download environments

