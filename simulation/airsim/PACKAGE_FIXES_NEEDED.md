# AirSim Package Fixes - Build Instructions

**Status:** Packages renamed, need to be rebuilt

## Summary

Fixed package naming conflicts and removed obsolete components. All AirSim packages now have unique names to avoid conflicts with Gazebo packages.

## Packages That Need Building

Run this command to build all AirSim packages:

```bash
cd ws_ros2
colcon build --packages-select \
  airsim_camera_bridge \
  airsim_enemy_visualizer \
  ally_visualizer \
  enemy_control
source install/setup.bash
```

## Changes Made

### 1. ✅ Camera Bridge Renamed
- **Old**: `camera_bridge`
- **New**: `airsim_camera_bridge`
- **Reason**: Avoid generic name, make it clear it's for AirSim
- **Location**: `simulation/airsim/debug/airsim_camera_bridge/`

### 2. ✅ Enemy Visualizer Renamed
- **Old**: `enemy_visualizer` (conflicted with Gazebo's package)
- **New**: `airsim_enemy_visualizer`
- **Reason**: Both Gazebo and AirSim had packages with same name
- **Location**: `simulation/airsim/debug/airsim_enemy_visualizer/`

### 3. ✅ Viz Translator Removed
- **Old**: `viz_translator` package
- **Removed**: This package is obsolete
- **Reason**: Now use `ally_visualizer` + `airsim_enemy_visualizer` instead
- **Action**: Removed launch code from `engine.py`

### 4. Enemy Control Package
- **Name**: `enemy_control` (unchanged)
- **Location**: `simulation/common/debug/enemy_control/`
- **Status**: Needs to be built
- **Shared**: Used by both Gazebo and AirSim

### 5. Ally Visualizer Package
- **Name**: `ally_visualizer` (unchanged)
- **Location**: `simulation/common/debug/ally_visualizer/`
- **Status**: Should already be built
- **Shared**: Used by both Gazebo and AirSim

## Issues Remaining

### Issue: AirSim Multi-Drone TCP Port
**Problem**: Enemy PX4 instance waiting on TCP port 4561, but AirSim only supports port 4560

**From your error output:**
```
INFO  [simulator_mavlink] Waiting for simulator to accept connection on TCP port 4561
```

**Root Cause**: AirSim LockStep mode only supports ONE TCP connection (port 4560)

**Working Commit Behavior**: Used SimpleFlight for Enemy (no PX4), only Ally had PX4

**Solutions:**

**Option A - Single PX4 Drone (RECOMMENDED)**:
- Ally: PX4Multirotor (full autopilot)
- Enemy: SimpleFlight (controlled via AirSim Python API)
- Update settings template to use SimpleFlight for Enemy
- No PX4 instance for Enemy

**Option B - Disable LockStep for Multi-Drone**:
- Both drones use PX4
- Disable LockStep in settings.json
- Use different TCP ports (4560, 4561)
- Less deterministic simulation

**Option C - Document Limitation**:
- AirSim multi-drone only supports 1 PX4 drone
- Single-drone mode works perfectly
- Multi-drone requires SimpleFlight for Enemy

## Recommended: Use SimpleFlight for Enemy

Update `settings_template_multi.json`:
```json
"Enemy": {
  "VehicleType": "SimpleFlight",  // ← No PX4, use AirSim's flight controller
  "X": {{ENEMY_X}},
  "Y": {{ENEMY_Y}},
  "Z": {{ENEMY_Z}},
  "Yaw": {{ENEMY_YAW}}
}
```

Then don't launch PX4 for Enemy - control it via `enemy_control` using AirSim Python API.

## Testing After Build

```bash
# Clean old processes
pkill -f "px4"
pkill -f "Blocks"

# Test single-drone first (should work perfectly)
./scripts/launch.sh --simulator airsim

# Test multi-drone (will need SimpleFlight solution)
./scripts/launch.sh --simulator airsim --mode multi --debug
```

## Expected Output After Fixes

```
[AirSim] ✓ Camera bridge launched successfully
[AirSim] ✓ Ally visualizer started
[AirSim] ✓ Enemy visualizer started  # Will show "AirSim" not "Gazebo"
[Launcher] ✓ Enemy offboard control started
```

No more "No executable found" or "Package not found" errors!
