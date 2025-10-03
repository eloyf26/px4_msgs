# AirSim Configuration for Halcon1

## Overview

This directory contains the AirSim configuration file for running Halcon1 system with AirSim + Unreal Engine simulation.

## Setup

### 1. Copy settings.json to AirSim Config Directory

AirSim reads its configuration from a specific directory:

**Linux/WSL:**
```bash
mkdir -p ~/Documents/AirSim
cp config/airsim/settings.json ~/Documents/AirSim/
```

**Windows:**
```powershell
mkdir $env:USERPROFILE\Documents\AirSim
copy config\airsim\settings.json $env:USERPROFILE\Documents\AirSim\
```

### 2. Verify Configuration

After copying, the file should be located at:
- Linux/WSL: `~/Documents/AirSim/settings.json`
- Windows: `C:\Users\<YourUsername>\Documents\AirSim\settings.json`

## Configuration Details

### Vehicle: "Ally" (PX4Multirotor)

This is the friendly drone controlled by PX4 and your Halcon1 ROS2 nodes.

**Key Settings:**
- **VehicleType**: `PX4Multirotor` - Uses PX4 flight controller (not SimpleFlight)
- **UseTcp**: `true` - MAVLink communication over TCP
- **TcpPort**: `4560` - PX4 will connect to this port
- **LockStep**: `true` - **Critical!** Synchronizes physics with PX4 time
- **Sensors**: IMU, GPS, Magnetometer, Barometer all enabled
- **Camera**: 640x480, 60° FOV (matches Gazebo configuration)

**Position**: Origin (0, 0, 0)

### Vehicle: "Enemy" (SimpleFlight)

This is the target drone using AirSim's built-in SimpleFlight controller.

**Key Settings:**
- **VehicleType**: `SimpleFlight` - AirSim's internal controller
- **Position**: (5, 0, 0) - 5 meters in front of Ally

You can control this drone programmatically via AirSim Python API or manually via keyboard.

## Camera Configuration

The camera is mounted on the "Ally" drone:
- **Name**: `front_center`
- **Resolution**: 640x480 (same as Gazebo)
- **FOV**: 60 degrees (same as Gazebo)
- **Position**: 0.3m in front of drone center
- **Orientation**: Facing forward (pitch=0, roll=0, yaw=0)

This ensures that camera images from AirSim match those from Gazebo for YOLO detection compatibility.

## ROS2 Topic Mapping

When using `airsim_ros_pkgs`, topics are remapped as follows:

**AirSim Topic** → **Halcon1 Topic**
- `/airsim_node/Ally/front_center/Scene` → `/camera/image`
- `/airsim_node/Ally/front_center/camera_info` → `/camera/camera_info`

This is handled by the launch script with `-r` (remap) arguments.

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

### Add More Drones

To add additional drones, add new vehicles to the `Vehicles` section:

```json
"Vehicles": {
  "Ally": { ... },
  "Enemy": { ... },
  "Enemy2": {
    "VehicleType": "SimpleFlight",
    "X": -5, "Y": 5, "Z": 0
  }
}
```

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

### PX4 Not Connecting to AirSim

**Symptoms**: PX4 console shows `Waiting for simulator...` indefinitely

**Solutions**:
1. Ensure AirSim is running and fully loaded before starting PX4
2. Check that `TcpPort: 4560` matches PX4 expectations
3. Verify `LockStep: true` is set
4. Check firewall settings (allow TCP 4560)

### Camera Topics Not Appearing

**Symptoms**: `/camera/image` topic doesn't exist after starting `airsim_ros_pkgs`

**Solutions**:
1. Verify camera name matches: `front_center`
2. Check vehicle name matches: `Ally`
3. Ensure AirSim is running with this settings.json
4. Check `airsim_ros_pkgs` remapping arguments

### Drone Falls Immediately After Takeoff

**Symptoms**: Drone arms, takes off, then crashes

**Solutions**:
1. Ensure `LockStep: true` is enabled
2. Check PX4 console for sensor errors
3. Verify all sensors are enabled (IMU, GPS, Barometer, Magnetometer)
4. Try slower takeoff velocity in PX4 parameters

## References

- [AirSim Settings Documentation](https://microsoft.github.io/AirSim/settings/)
- [PX4 AirSim Setup](https://microsoft.github.io/AirSim/px4_setup/)
- [LockStep Mode Details](https://microsoft.github.io/AirSim/px4_sitl/)

