# Halcon1 System Architecture

## Overview

Halcon1 is an autonomous drone interception system built on a **simulator-agnostic architecture**. The core detection, tracking, and guidance logic works identically across Gazebo, AirSim, Isaac Sim, and real hardware without code changes.

## Design Principles

### 1. Separation of Concerns

The system separates **what to do** (core logic) from **how to simulate/sense** (environment layer):

```
┌─────────────────────────────────────────────────────────────┐
│                   HALCON1 CORE LOGIC                        │
│           (Detection → Tracking → Guidance)                 │
│                                                             │
│  • Platform-agnostic ROS2 nodes                            │
│  • Standard topic interfaces only                          │
│  • Works on: Gazebo, AirSim, Isaac, Real Hardware          │
└─────────────────────────────────────────────────────────────┘
                            ↕
              Standard ROS2 Topics Interface
          (/camera/image, /fmu/out/*, /fmu/in/*)
                            ↕
┌─────────────────────────────────────────────────────────────┐
│              ENVIRONMENT ABSTRACTION LAYER                  │
│                 (SimulationEngine Interface)                │
│                                                             │
│  Gazebo Engine    │  AirSim Engine  │  Hardware Adapter    │
│  - ros_gz_bridge  │  - camera_bridge│  - Real camera driver│
│  - Gazebo topics  │  - AirSim API   │  - Real PX4/MAVLink  │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                  PHYSICS/SENSOR LAYER                       │
│                                                             │
│  Gazebo Harmonic  │  AirSim/Unreal  │  Real Drone Hardware │
└─────────────────────────────────────────────────────────────┘
```

### 2. Plugin Architecture

All environments (simulators and hardware) implement the `SimulationEngine` interface:

```python
class SimulationEngine(ABC):
    @abstractmethod
    def validate_installation() -> Tuple[bool, str]

    @abstractmethod
    def launch_simulator() -> bool

    @abstractmethod
    def launch_bridges() -> bool

    @abstractmethod
    def get_camera_topic(drone_name: str) -> str

    @abstractmethod
    def get_px4_connection_config(instance_id: int) -> Dict

    @abstractmethod
    def cleanup() -> bool
```

This enables:
- ✅ Adding new simulators without touching core code
- ✅ Testing on fast simulator (Gazebo), deploying on realistic one (AirSim)
- ✅ Seamless transition from simulation to real hardware

### 3. Encapsulation

Core Halcon1 nodes **never import** from `src/ros2/simulation/`. They only use standard ROS2 topics, making them completely environment-agnostic.

## System Components

### Core Pipeline (src/ros2/modules/)

#### 1. Detection Module (`detection`)
- **Input:** `/camera/image` (sensor_msgs/Image)
- **Algorithm:** YOLOv8 object detection
- **Output:** `/enemy/detection` (msgs/Detection)
- **Purpose:** Detect enemy drones in camera frame, output 2D bounding box

#### 2. Tracking Module (`tracking`)
- **Input:**
  - `/enemy/detection` (msgs/Detection)
  - `/camera/camera_info` (sensor_msgs/CameraInfo)
  - `/fmu/out/vehicle_odometry` (px4_msgs/VehicleOdometry)
- **Algorithm:** Pinhole camera model + depth estimation
- **Output:** `/enemy/tracked` (msgs/TrackedObject)
- **Purpose:** Transform 2D pixel coordinates → 3D world coordinates

#### 3. Guidance Module (`guidance`)
- **Input:**
  - `/enemy/tracked` (msgs/TrackedObject)
  - `/fmu/out/vehicle_odometry` (px4_msgs/VehicleOdometry)
- **Algorithm:** Kalman Filter prediction + Proportional Navigation
- **Output:** `/fmu/in/trajectory_setpoint` (px4_msgs/TrajectorySetpoint)
- **Purpose:** Predict enemy trajectory, generate interception commands

### Shared Libraries (src/lib/)

#### 1. Algorithms (`algorithms`)
- Kalman Filter implementation
- Proportional Navigation guidance law
- State estimation utilities

#### 2. Transforms (`transforms`)
- Camera-to-world coordinate transformations
- NED ↔ ENU frame conversions
- Quaternion utilities

#### 3. Common Types (`common_types`)
- Shared data structures
- Type definitions

### Environment Layer (src/ros2/simulation/)

#### Gazebo Engine (`simulation/gazebo/`)
- **Bridge:** ros_gz (12 ROS2 packages)
- **Connection:** Direct ROS2 topic bridging
- **Physics:** Gazebo Harmonic (ODE/Bullet)
- **Use Case:** Fast iteration, CI/CD, development

#### AirSim Engine (`simulation/airsim/`)
- **Bridges:**
  - `camera_bridge`: AirSim camera → ROS2
  - `viz_translator`: PX4 odometry → RViz markers
- **Connection:** AirSim Python API
- **Physics:** Unreal Engine + PhysX
- **Use Case:** Photo-realistic rendering, CV research

#### Hardware Adapter (Future)
- **Bridge:** Native ROS2 camera drivers
- **Connection:** MAVLink to real PX4
- **Purpose:** Deploy on real drones

### PX4 Integration (src/ros2/external/)

#### px4_msgs
- 300+ PX4 message definitions
- Vehicle odometry, trajectory setpoints, sensor data

### Debug Tools (src/ros2/modules/debug/)

#### ally_visualizer
- Publishes RViz markers for ally drone
- Shows position, velocity vectors, orientation and annotated detection image

#### enemy_visualizer (when available)
- Publishes RViz markers for enemy drone
- Shows tracked position, predicted trajectory

## Data Flow

### Detailed System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ SIMULATOR / HARDWARE                                            │
│  - Gazebo Harmonic OR AirSim/Unreal OR Real Hardware            │
│  - Physics simulation (gravity, aerodynamics, collisions)       │
│  - Sensor simulation (IMU, GPS, Barometer, Magnetometer)        │
│  - Camera rendering                                             │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ MAVLink (TCP/UDP)                  │ Simulator Topics
             │ (sensor data → PX4)                │ (camera/image)
             │ (motor commands ← PX4)             │
             ↓                                    ↓
┌─────────────────────────────┐     ┌──────────────────────────────┐
│ PX4 SITL / Real Firmware    │     │ Camera Bridge                │
│  - Flight controller SW     │     │  - ros_gz_bridge (Gazebo)    │
│  - Sensor fusion            │     │  - camera_bridge (AirSim)    │
│  - Attitude/position ctrl   │     │  - usb_cam (Hardware)        │
│  - Mission planning         │     │  → /camera/image (ROS2)      │
│  - Safety features          │     │  → /camera/camera_info       │
└─────────────┬───────────────┘     └──────────────┬───────────────┘
              │                                     │
              │ uXRCE-DDS (UDP 8888)               │
              │ (PX4 uORB ↔ ROS2 DDS)              │
              ↓                                     │
┌─────────────────────────────┐                    │
│ MicroXRCE-DDS Agent         │                    │
│  - Translates uORB → DDS    │                    │
│  - PX4-ROS2 bridge          │                    │
└─────────────┬───────────────┘                    │
              │                                     │
              │ DDS Protocol (ROS2 Topics)         │
              ↓                                     ↓
┌──────────────────────────────────────────────────────────────────┐
│ ROS2 Network (DDS Middleware)                                    │
│                                                                  │
│  PX4 → ROS2 Topics:                                             │
│    /fmu/out/vehicle_odometry (pose, velocity, orientation)      │
│    /fmu/out/vehicle_status (armed, flight mode)                 │
│                                                                  │
│  ROS2 → PX4 Topics:                                             │
│    /fmu/in/trajectory_setpoint (position/velocity/accel)        │
│    /fmu/in/offboard_control_mode (control mode flags)           │
│    /fmu/in/vehicle_command (arm, takeoff, land)                 │
│                                                                  │
│  Sensor Topics:                                                 │
│    /camera/image (raw camera feed, 30 Hz)                       │
│    /camera/camera_info (intrinsics, calibration)                │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────────────┐
│ Halcon1 ROS2 Nodes (Core Pipeline)                              │
│                                                                  │
│  detection_node:                                                │
│    - Subscribes: /camera/image                                  │
│    - Publishes: /enemy/detection (bbox: x, y, w, h)             │
│    - Algorithm: YOLOv11n drone detection                        │
│                                                                  │
│  tracking_node:                                                 │
│    - Subscribes: /enemy/detection, /fmu/out/vehicle_odometry,   │
│                  /camera/camera_info                            │
│    - Publishes: /enemy/pose (world coordinates x, y, z)         │
│    - Algorithm: Pinhole camera model + depth estimation         │
│                                                                  │
│  guidance_node:                                                 │
│    - Subscribes: /enemy/pose, /fmu/out/vehicle_odometry         │
│    - Publishes: /fmu/in/trajectory_setpoint (acceleration)      │
│    - Algorithm: Kalman Filter + Proportional Navigation         │
└──────────────────────────────────────────────────────────────────┘
```

### Pipeline Flow Summary

```
Camera Sensor (Simulator or Real)
         ↓
   /camera/image (30 Hz)
         ↓
   Detection Node (YOLOv11n)
         ↓
   /enemy/detection (x, y, w, h)
         ↓
   Tracking Node (Camera Transform)
         ↓
   /enemy/pose (world x, y, z)
         ↓
   Guidance Node (Kalman + ProNav)
         ↓
   /fmu/in/trajectory_setpoint (ax, ay, az)
         ↓
   PX4 Autopilot (via MicroXRCE-DDS)
         ↓
   Drone Motors
```

### Key ROS2 Topics

| Topic | Type | Rate | Publisher | Subscribers |
|-------|------|------|-----------|-------------|
| `/camera/image` | sensor_msgs/Image | 30 Hz | Camera bridge | Detection |
| `/camera/camera_info` | sensor_msgs/CameraInfo | 30 Hz | Camera bridge | Tracking |
| `/enemy/detection` | msgs/Detection | 10 Hz | Detection | Tracking |
| `/enemy/tracked` | msgs/TrackedObject | 10 Hz | Tracking | Guidance |
| `/fmu/in/trajectory_setpoint` | px4_msgs/TrajectorySetpoint | 10 Hz | Guidance | PX4 |
| `/fmu/out/vehicle_odometry` | px4_msgs/VehicleOdometry | 50 Hz | PX4 | Tracking, Guidance |

## Directory Structure

```
halcon1-system/
├── src/
│   ├── lib/                      # Shared libraries
│   │   ├── algorithms/           # Kalman, ProNav
│   │   ├── transforms/           # Coordinate transforms
│   │   └── common_types/         # Type definitions
│   └── ros2/
│       ├── modules/              # Core Halcon1 logic
│       │   ├── detection/        # YOLO detection
│       │   ├── tracking/         # Camera transforms
│       │   ├── guidance/         # Kalman + ProNav
│       │   ├── msgs/             # Message definitions
│       │   ├── bringup/          # Launch files
│       │   └── debug/            # Visualization tools
│       ├── external/             # PX4 packages
│       │   └── px4_msgs/         # PX4 messages
│       └── simulation/           # Environment-specific
│           ├── common/           # SimulationEngine interface
│           ├── gazebo/           # Gazebo implementation
│           └── airsim/           # AirSim implementation
├── external/                     # Git submodules
│   ├── PX4-Autopilot/            # PX4 flight stack
│   └── Micro-XRCE-DDS-Agent/     # PX4-ROS2 bridge
├── scripts/                      # Launch/utility scripts
└── docs/                         # Documentation
```

## Coordinate Frames

### 1. Camera Frame (Detection)
- **Origin:** Camera optical center
- **X-axis:** Right
- **Y-axis:** Down
- **Z-axis:** Forward (optical axis)
- **Units:** Pixels (2D image coordinates)

### 2. Body Frame (PX4)
- **Origin:** Drone center of mass
- **X-axis:** Forward (nose)
- **Y-axis:** Right (starboard)
- **Z-axis:** Down
- **Units:** Meters

### 3. World Frame (Tracking/Guidance)
- **Origin:** Simulation/world origin
- **Convention:** ENU (East-North-Up) or NED (North-East-Down) depending on simulator
- **Units:** Meters

### Transformation Chain
```
Camera Pixels → Camera 3D → Body Frame → World Frame
```

See `src/ros2/modules/tracking/REFERENCE_FRAMES.md` for detailed transformations.


## Extension Points

### Adding New Detection Algorithms
Replace `detection/detection_algorithm.py` while keeping the same topic interface.

### Adding New Guidance Laws
Replace `guidance/px4_command_generator.py` with new guidance algorithm.

### Adding New Simulators
Implement `SimulationEngine` interface (see docs/SIMULATION.md).

### Adding Real Hardware
Create hardware adapter implementing `SimulationEngine` (see docs/SIMULATION.md).

## See Also

- [Installation Guide](INSTALLATION.md) - Setup instructions
- [Simulation Guide](SIMULATION.md) - How to add simulators/hardware
- [Algorithm Details](ALGORITHMS.md) - Deep dive into detection/tracking/guidance
- [Development Guide](DEVELOPMENT.md) - Building and testing
