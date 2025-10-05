# Halcon1 Package Structure

## Organization Philosophy

The Halcon1 system is organized into clear functional categories:

```
Halcon1/
├── pipeline/        # Core 3-stage processing pipeline
├── lib/             # Shared libraries (reusable utilities)
├── debug/           # Debug visualization tools
├── msgs/            # Custom message definitions
└── bringup/         # Launch files
```

## Packages

### Pipeline (Detection → Tracking → Guidance)

**Location:** `Halcon1/pipeline/`

1. **detection** - YOLOv11 drone detection from camera images
   - Subscribes: `/camera/image`
   - Publishes: `/enemy/detection`

2. **tracking** - Camera-to-world coordinate transformation
   - Subscribes: `/enemy/detection`, `/camera/camera_info`, `/fmu/out/vehicle_odometry`
   - Publishes: `/enemy/pose`
   - Contains: Camera intrinsics, pixel-to-world transform

3. **guidance** - Kalman Filter + Proportional Navigation
   - Subscribes: `/enemy/tracked`, `/fmu/out/vehicle_odometry`
   - Publishes: `/interception/command`, `/fmu/in/trajectory_setpoint`
   - Depends on: `algorithms` library

### Shared Libraries

**Location:** `Halcon1/lib/`

1. **transforms** (formerly `utils`)
   - Coordinate frame transformations (NED ↔ ENU)
   - PX4 quaternion conversions
   - Used by: tracking, ally_visualizer, simulation packages

2. **common_types**
   - Shared Python dataclasses (`DronePose`, `DetectionResult`, etc.)
   - Used by: all pipeline modules, transforms

3. **algorithms** (moved from `guidance/utils/`)
   - Kalman Filter implementation
   - Proportional Navigation implementation
   - Reusable math/control algorithms
   - Used by: guidance

### Debug Tools

**Location:** `Halcon1/debug/`

1. **ally_visualizer**
   - Converts ally PX4 messages → RViz debug topics
   - Publishes: `/debug/ally/pose`, `/debug/ally/path`, etc.
   - **Works with real hardware** (not simulation-only)
   - No symlink needed - directly in Halcon1

### Messages

**Location:** `Halcon1/msgs/`

- Custom ROS2 message definitions
- `DroneDetection.msg` - Bounding box detection

### Bringup

**Location:** `Halcon1/bringup/`

- Launch files for starting the full pipeline
- `pipeline.launch.py` - Launches detection, tracking, guidance

## Dependencies

```
Pipeline dependencies:
detection → common_types, msgs
tracking → common_types, transforms, msgs
guidance → common_types, algorithms, msgs

Library dependencies:
transforms → common_types
algorithms → (standalone)
common_types → (standalone)

Debug dependencies:
ally_visualizer → transforms
```

## Why This Structure?

### Before (Issues):
- ❌ `modules/utils/` confused with `guidance/utils/`
- ❌ Shared libraries mixed with pipeline modules
- ❌ "utils" name too generic
- ❌ No clear separation of concerns

### After (Benefits):
- ✅ Clear separation: `pipeline/` vs `lib/` vs `debug/`
- ✅ Descriptive names: `transforms`, `algorithms`
- ✅ Scalable: Easy to add new pipeline stages or libraries
- ✅ No naming conflicts
- ✅ Logical hierarchy

## External Symlinks

**Location:** `ws_ros2/src/symlinks/`

Symlinks are **only** for packages outside `Halcon1/`:

```
symlinks/
├── enemy_control          # Common (shared across simulators)
├── gazebo/               # Gazebo-specific
│   ├── enemy_visualizer
│   └── ros_gz
└── airsim/               # AirSim-specific
    ├── camera_bridge
    └── viz_translator
```

**Note:** `ally_visualizer` has NO symlink - it's already in `Halcon1/debug/`
