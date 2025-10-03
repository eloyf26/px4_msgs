# Halcon1 System Architecture and Development Plan

## Overview

This document outlines the architecture of the Halcon1 autonomous drone interception system and the plan to support multiple simulation environments (Gazebo, AirSim) while maintaining compatibility with real hardware deployment.

## Table of Contents

1. [PX4 Simulation Architecture](#px4-simulation-architecture)
2. [Current Architecture (Gazebo)](#current-architecture-gazebo--px4--ros2)
3. [Target Architecture (AirSim)](#target-architecture-airsim--px4--ros2)
4. [Real Hardware Architecture](#real-hardware-architecture)
5. [Phase 1: AirSim Integration](#phase-1-airsim-integration)
6. [Phase 2: Advanced Navigation](#phase-2-advanced-navigation)

---

## PX4 Simulation Architecture

### Core Principle: PX4 is Simulator-Agnostic

**Key Insight**: PX4 (the flight controller software) doesn't care what simulator is running. It only needs:

1. **Sensor data IN** (IMU, GPS, barometer, magnetometer, etc.)
2. **Motor commands OUT** (PWM signals to motors)

The simulator's responsibility:
1. Send simulated sensor data to PX4 (via MAVLink protocol)
2. Receive motor commands from PX4 (via MAVLink protocol)
3. Update physics simulation based on motor commands
4. Generate camera images and other sensor data
5. Repeat the cycle in real-time or faster

### Communication Protocols

- **MAVLink**: Binary protocol for communicating with drones
  - Used between simulator ↔ PX4
  - Transports: TCP, UDP, serial

- **uXRCE-DDS**: Micro XRCE-DDS protocol
  - Used between PX4 ↔ ROS2
  - Translates PX4 uORB topics ↔ ROS2 DDS topics
  - Requires MicroXRCE-DDS Agent running

- **DDS (Data Distribution Service)**: ROS2 middleware
  - Used between ROS2 nodes
  - Publish/subscribe architecture

---

## Current Architecture (Gazebo + PX4 + ROS2)

```
┌─────────────────────────────────────────────────────────────────┐
│ GAZEBO (Physics Engine)                                         │
│  - Simulates drone physics (gravity, aerodynamics, collisions)  │
│  - Simulates sensors (IMU, GPS, Barometer, Magnetometer)       │
│  - Simulates camera with realistic rendering                    │
│  - Provides 3D environment                                       │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ MAVLink over TCP/UDP               │ Gazebo Topics
             │ (sensor data → PX4)                │ (camera/image)
             │ (motor commands ← PX4)             │
             │ Port: 14560                        │
             ↓                                    ↓
┌─────────────────────────────┐     ┌──────────────────────────────┐
│ PX4 SITL                    │     │ ros_gz_bridge                │
│  - Flight controller SW     │     │  - Bridges Gazebo → ROS2     │
│  - Reads simulated sensors  │     │  - Topic remapping           │
│  - Attitude/position ctrl   │     │  - Message conversion        │
│  - Computes motor outputs   │     │  → /camera/image (ROS2)      │
│  - Mission planning         │     └──────────────────────────────┘
│  - Safety features          │                  │
└─────────────┬───────────────┘                  │
              │                                   │
              │ uXRCE-DDS                        │
              │ UDP Port: 8888                   │
              │ (PX4 uORB topics)                │
              ↓                                   │
┌─────────────────────────────┐                  │
│ MicroXRCE-DDS Agent         │                  │
│  - Translates uORB → DDS    │                  │
│  - Proxy for PX4 topics     │                  │
│  - UDP listener on 8888     │                  │
└─────────────┬───────────────┘                  │
              │                                   │
              │ DDS Protocol (ROS2 Topics)       │
              ↓                                   ↓
┌──────────────────────────────────────────────────────────────────┐
│ ROS2 Network (DDS Middleware)                                    │
│                                                                  │
│  PX4 → ROS2 Topics:                                             │
│    - /fmu/out/vehicle_odometry (pose, velocity)                 │
│    - /fmu/out/vehicle_status (armed, mode)                      │
│    - /fmu/out/vehicle_local_position                            │
│                                                                  │
│  ROS2 → PX4 Topics:                                             │
│    - /fmu/in/trajectory_setpoint (position/velocity/accel)      │
│    - /fmu/in/offboard_control_mode (control mode flags)         │
│    - /fmu/in/vehicle_command (arm, takeoff, land, etc.)         │
│                                                                  │
│  Sensor Topics (Gazebo → ROS2):                                 │
│    - /camera/image (raw camera feed)                            │
│    - /camera/camera_info (calibration data)                     │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────────────┐
│ Halcon1 ROS2 Nodes                                              │
│                                                                  │
│  halcon1_detection:                                             │
│    - Subscribes: /camera/image                                  │
│    - Publishes: /enemy/detection (bounding box, confidence)     │
│    - Algorithm: YOLOv11n drone detection                        │
│                                                                  │
│  halcon1_tracking:                                              │
│    - Subscribes: /enemy/detection, /fmu/out/vehicle_odometry    │
│    - Publishes: /enemy/pose (world coordinates)                 │
│    - Algorithm: Camera-to-world coordinate transformation       │
│                                                                  │
│  halcon1_guidance:                                              │
│    - Subscribes: /enemy/pose, /fmu/out/vehicle_odometry         │
│    - Publishes: /fmu/in/trajectory_setpoint                     │
│    - Algorithm: Kalman Filter + Proportional Navigation         │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow Example

1. **Gazebo** generates camera frame → `ros_gz_bridge` → `/camera/image` (ROS2)
2. **Gazebo** sends IMU/GPS data → MAVLink → **PX4 SITL**
3. **PX4** processes sensor fusion → publishes odometry → **MicroXRCE Agent** → `/fmu/out/vehicle_odometry` (ROS2)
4. **halcon1_detection** reads `/camera/image` → YOLO inference → `/enemy/detection`
5. **halcon1_tracking** reads `/enemy/detection` + `/fmu/out/vehicle_odometry` → coordinate transform → `/enemy/pose`
6. **halcon1_guidance** reads `/enemy/pose` → Kalman Filter + ProNav → `/fmu/in/trajectory_setpoint`
7. **MicroXRCE Agent** → PX4 receives setpoint → computes motor commands → MAVLink → **Gazebo**
8. **Gazebo** applies forces to drone → physics update → repeat

### Current Launch Process

The `launch_multi_terminal.sh` script orchestrates:

1. **MicroXRCE Agent** (UDP 8888)
2. **PX4 SITL** (launches Gazebo automatically, MAVLink 14560)
3. **Camera Bridge** (`ros_gz_bridge` for camera topics)
4. **Detection Node** (YOLO processing)
5. **Tracking Node** (coordinate transformation)
6. **Guidance Node** (interception control)
7. **RViz** (visualization)

---

## Target Architecture (AirSim + PX4 + ROS2)

```
┌─────────────────────────────────────────────────────────────────┐
│ UNREAL ENGINE + AirSim                                          │
│  - Photo-realistic graphics (Unreal Engine 4/5)                 │
│  - PhysX physics engine                                         │
│  - Simulates sensors (IMU, GPS, Barometer, Magnetometer)       │
│  - High-fidelity camera simulation                              │
│  - Custom environments (cities, buildings, terrain)             │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ MAVLink over TCP                   │ AirSim API
             │ (sensor data → PX4)                │ (simGetImages, etc.)
             │ (motor commands ← PX4)             │
             │ Port: 4560 (LockStep mode)         │
             ↓                                    ↓
┌─────────────────────────────┐     ┌──────────────────────────────┐
│ PX4 SITL                    │     │ airsim_ros_pkgs              │
│  - SAME binary as Gazebo!   │     │  - Bridges AirSim → ROS2     │
│  - Flight controller SW     │     │  - Python/C++ API wrapper    │
│  - Reads simulated sensors  │     │  - Topic remapping           │
│  - Computes motor outputs   │     │  → /camera/image (ROS2)      │
└─────────────┬───────────────┘     └──────────────────────────────┘
              │                                   │
              │ uXRCE-DDS (IDENTICAL!)           │
              │ UDP Port: 8888                   │
              ↓                                   │
┌─────────────────────────────┐                  │
│ MicroXRCE-DDS Agent         │                  │
│  - SAME as Gazebo setup!    │                  │
│  - No configuration changes │                  │
└─────────────┬───────────────┘                  │
              │                                   │
              │ DDS Protocol (SAME TOPICS!)      │
              ↓                                   ↓
┌──────────────────────────────────────────────────────────────────┐
│ ROS2 Network (IDENTICAL to Gazebo)                              │
│  - /fmu/out/vehicle_odometry                                    │
│  - /fmu/in/trajectory_setpoint                                  │
│  - /camera/image (from airsim_ros_pkgs instead)                 │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────────────┐
│ Halcon1 ROS2 Nodes (NO CODE CHANGES!)                           │
│  - halcon1_detection (reads /camera/image)                      │
│  - halcon1_tracking (reads /fmu/out/vehicle_odometry)           │
│  - halcon1_guidance (writes /fmu/in/trajectory_setpoint)        │
└──────────────────────────────────────────────────────────────────┘
```

### Key Differences from Gazebo

| Component | Gazebo | AirSim |
|-----------|--------|--------|
| Physics Engine | Custom (ODE/Bullet) | PhysX (NVIDIA) |
| Graphics | Ogre2/Ogre1 | Unreal Engine 4/5 |
| MAVLink Port | 14560 (UDP) | 4560 (TCP) |
| Camera Bridge | ros_gz_bridge | airsim_ros_pkgs |
| PX4 Binary | ✅ Same | ✅ Same |
| MicroXRCE Agent | ✅ Same | ✅ Same |
| ROS2 Topics | ✅ Same | ✅ Same |
| Halcon1 Nodes | ✅ Same | ✅ Same |

### AirSim Configuration

**settings.json** (must be placed in `~/Documents/AirSim/` or `%USERPROFILE%\Documents\AirSim\`):

```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",
  "ClockType": "SteppableClock",
  "Vehicles": {
    "Drone1": {
      "VehicleType": "PX4Multirotor",
      "UseSerial": false,
      "UseTcp": true,
      "TcpPort": 4560,
      "ControlIp": "localhost",
      "LockStep": true,
      "Sensors": {
        "Imu": { "SensorType": 2, "Enabled": true },
        "Gps": { "SensorType": 3, "Enabled": true },
        "Magnetometer": { "SensorType": 4, "Enabled": true },
        "Barometer": { "SensorType": 1, "Enabled": true }
      },
      "Cameras": {
        "front_center": {
          "CaptureSettings": [
            {
              "ImageType": 0,
              "Width": 640,
              "Height": 480,
              "FOV_Degrees": 60,
              "AutoExposureSpeed": 100,
              "MotionBlurAmount": 0
            }
          ],
          "X": 0.3,
          "Y": 0.0,
          "Z": 0.0,
          "Pitch": 0.0,
          "Roll": 0.0,
          "Yaw": 0.0
        }
      }
    }
  }
}
```

**Key Configuration Parameters**:

- `VehicleType: "PX4Multirotor"` - Use PX4 instead of SimpleFlight
- `UseTcp: true, TcpPort: 4560` - MAVLink over TCP
- `LockStep: true` - Synchronize physics with PX4 (critical for accurate simulation)
- Camera matches Gazebo specs: 640x480, 60° FOV

---

## Real Hardware Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ REAL DRONE HARDWARE                                             │
│  - Physical sensors (IMU, GPS, Barometer, Magnetometer)        │
│  - Physical camera (USB/CSI interface)                          │
│  - Physical motors and ESCs                                     │
│  - Pixhawk flight controller (PX4 firmware)                     │
│  - Companion computer (Raspberry Pi, Jetson, etc.)              │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ Serial/UART connection             │ USB/Ethernet
             │ (telemetry data ↔ PX4)            │ (camera stream)
             │                                    │
             ↓                                    ↓
┌─────────────────────────────┐     ┌──────────────────────────────┐
│ PX4 Firmware (on Pixhawk)   │     │ usb_cam / cv_camera         │
│  - SAME flight controller!  │     │  - V4L2 camera driver        │
│  - Reads REAL sensors       │     │  - Publishes to ROS2         │
│  - Controls REAL motors     │     │  → /camera/image (ROS2)      │
│  - Same algorithms as SITL  │     └──────────────────────────────┘
└─────────────┬───────────────┘                  │
              │                                   │
              │ uXRCE-DDS (SAME PROTOCOL!)       │
              │ Serial: /dev/ttyUSB0 or WiFi     │
              ↓                                   │
┌─────────────────────────────┐                  │
│ MicroXRCE-DDS Agent         │                  │
│  - Runs on companion PC     │                  │
│  - Serial or WiFi transport │                  │
│  - SAME as simulation!      │                  │
└─────────────┬───────────────┘                  │
              │                                   │
              │ DDS (SAME ROS2 TOPICS!)          │
              ↓                                   ↓
┌──────────────────────────────────────────────────────────────────┐
│ ROS2 Network (IDENTICAL!)                                        │
│  - /fmu/out/vehicle_odometry                                    │
│  - /fmu/in/trajectory_setpoint                                  │
│  - /camera/image (from real camera)                             │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────────────┐
│ Halcon1 ROS2 Nodes (STILL NO CODE CHANGES!)                     │
│  - halcon1_detection (reads /camera/image)                      │
│  - halcon1_tracking (reads /fmu/out/vehicle_odometry)           │
│  - halcon1_guidance (writes /fmu/in/trajectory_setpoint)        │
└──────────────────────────────────────────────────────────────────┘
```

### Real Hardware Setup

1. **Flash PX4 firmware** to Pixhawk board
2. **Configure serial connection** between Pixhawk and companion computer
3. **Start MicroXRCE Agent** on companion computer (serial or WiFi transport)
4. **Start camera driver** (usb_cam, cv_camera, etc.)
5. **Run Halcon1 nodes** (identical to simulation!)

---

## Phase 1: AirSim Integration

**Goal**: Add AirSim simulation support while maintaining Gazebo compatibility.

**Principle**: No changes to Halcon1 ROS2 nodes. Only simulator backend changes.

### Prerequisites

1. **Unreal Engine + AirSim**
   - Prebuilt binary environment (recommended): [AirSim Releases](https://github.com/microsoft/AirSim/releases)
   - OR build from source for custom environments

2. **airsim_ros_pkgs**
   - ROS2 wrapper for AirSim API
   - GitHub: https://github.com/microsoft/airsim_ros_pkgs
   - May need fixes for ROS2 Humble compatibility

3. **PX4-Autopilot**
   - Already installed (external/PX4-Autopilot)
   - Same binary works for both Gazebo and AirSim

### Implementation Steps

#### Step 1: Install AirSim Environment

**Option A: Prebuilt Binaries** (Fastest)
```bash
# Download from https://github.com/microsoft/AirSim/releases
# Example: Blocks environment
wget https://github.com/microsoft/AirSim/releases/download/v1.8.1/Blocks.zip
unzip Blocks.zip -d ~/AirSimEnvironments/
```

**Option B: Build from Source** (For custom environments)
```bash
# Follow: https://microsoft.github.io/AirSim/build_linux/
git clone https://github.com/Microsoft/AirSim.git
cd AirSim
./setup.sh
./build.sh
# Then build Unreal Engine project
```

**Test baseline**:
```bash
~/AirSimEnvironments/Blocks/LinuxBlocks.sh
# Should open Unreal Engine window with SimpleFlight drone
```

#### Step 2: Install airsim_ros_pkgs

```bash
cd /home/eloyfernandez/drone_ws/halcon1-system/ws_ros2/src
git clone https://github.com/microsoft/airsim_ros_pkgs.git

# Build for ROS2 Humble
cd /home/eloyfernandez/drone_ws/halcon1-system/ws_ros2
source /opt/ros/humble/setup.bash
colcon build --packages-select airsim_ros_pkgs

# Test
source install/setup.bash
ros2 pkg list | grep airsim
```

**Note**: airsim_ros_pkgs may need updates for ROS2 Humble. Common issues:
- Include path fixes for rclcpp
- Message type conversions
- CMakeLists.txt dependencies

#### Step 3: Configure AirSim for PX4

Create `config/airsim/settings.json`:

```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",
  "ClockType": "SteppableClock",
  "ViewMode": "SpringArmChase",
  "Vehicles": {
    "Ally": {
      "VehicleType": "PX4Multirotor",
      "UseSerial": false,
      "UseTcp": true,
      "TcpPort": 4560,
      "ControlIp": "127.0.0.1",
      "LockStep": true,
      "X": 0, "Y": 0, "Z": 0,
      "Pitch": 0, "Roll": 0, "Yaw": 0,
      "Sensors": {
        "Imu": {
          "SensorType": 2,
          "Enabled": true
        },
        "Gps": {
          "SensorType": 3,
          "Enabled": true
        },
        "Magnetometer": {
          "SensorType": 4,
          "Enabled": true
        },
        "Barometer": {
          "SensorType": 1,
          "Enabled": true
        }
      },
      "Cameras": {
        "front_center": {
          "CaptureSettings": [
            {
              "ImageType": 0,
              "Width": 640,
              "Height": 480,
              "FOV_Degrees": 60,
              "AutoExposureSpeed": 100,
              "AutoExposureMaxBrightness": 0.64,
              "AutoExposureMinBrightness": 0.03,
              "MotionBlurAmount": 0,
              "TargetGamma": 1.0
            }
          ],
          "X": 0.3,
          "Y": 0.0,
          "Z": 0.0,
          "Pitch": 0.0,
          "Roll": 0.0,
          "Yaw": 0.0
        }
      }
    }
  }
}
```

Copy to AirSim config directory:
```bash
mkdir -p ~/Documents/AirSim
cp config/airsim/settings.json ~/Documents/AirSim/
```

#### Step 4: Test PX4 ↔ AirSim Connection

**Terminal 1: Start AirSim**
```bash
~/AirSimEnvironments/Blocks/LinuxBlocks.sh
# Wait for Unreal Engine to load
# Should see "Waiting for connection" in AirSim HUD
```

**Terminal 2: Start PX4 SITL**
```bash
cd /home/eloyfernandez/drone_ws/halcon1-system/external/PX4-Autopilot

# No GPS mode (for indoor environments without GPS)
ENABLE_LOCKSTEP_SCHEDULER=yes PX4_SIM_MODEL=none ./build/px4_sitl_default/bin/px4

# OR with GPS (for outdoor environments)
# ENABLE_LOCKSTEP_SCHEDULER=yes PX4_SIM_MODEL=none ./build/px4_sitl_default/bin/px4 -s etc/init.d-posix/rcS
```

**Verify connection**:
- PX4 console should show: `INFO [simulator] Simulator connected on TCP port 4560`
- AirSim HUD should change from "Waiting" to showing drone info

**Test with QGroundControl**:
1. Open QGroundControl
2. Should auto-connect to PX4 on UDP 14550
3. Try arming: `commander arm` in PX4 console
4. Try takeoff: `commander takeoff` in PX4 console
5. Drone should takeoff in AirSim

#### Step 5: Test Camera Bridge

**Terminal 3: Start airsim_ros_pkgs**
```bash
cd /home/eloyfernandez/drone_ws/halcon1-system/ws_ros2
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run airsim_ros_pkgs airsim_node --ros-args \
  -p host_ip:=localhost \
  -r /airsim_node/Ally/front_center/Scene:=/camera/image \
  -r /airsim_node/Ally/front_center/camera_info:=/camera/camera_info
```

**Verify camera topics**:
```bash
# Terminal 4
ros2 topic list | grep camera
# Should show:
# /camera/image
# /camera/camera_info

ros2 topic hz /camera/image
# Should show ~30 Hz

ros2 run rqt_image_view rqt_image_view
# Select /camera/image
# Should see AirSim camera view
```

#### Step 6: Test Full Halcon1 Pipeline

**Terminal 5: Start MicroXRCE Agent**
```bash
cd /home/eloyfernandez/drone_ws/halcon1-system
./external/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent udp4 -p 8888
```

**Verify PX4 topics**:
```bash
ros2 topic list | grep fmu
# Should show all /fmu/in/* and /fmu/out/* topics

ros2 topic echo /fmu/out/vehicle_odometry --once
# Should show current pose/velocity
```

**Terminal 6: Start Detection Node**
```bash
cd /home/eloyfernandez/drone_ws/halcon1-system/ws_ros2
source /opt/ros/humble/setup.bash
source install/setup.bash
source venv/bin/activate

ros2 run halcon1_detection detection_node
```

**Terminal 7: Start Tracking Node**
```bash
ros2 run halcon1_tracking tracking_node
```

**Terminal 8: Start Guidance Node**
```bash
ros2 run halcon1_guidance guidance_node
```

**Verify data flow**:
```bash
ros2 topic hz /enemy/detection    # Should see detections when enemy in view
ros2 topic hz /enemy/pose         # Should see world coordinates
ros2 topic hz /fmu/in/trajectory_setpoint  # Should see guidance commands
```

#### Step 7: Create Launch Script

Create `scripts/launch_airsim.sh` (similar structure to `launch_multi_terminal.sh`):

```bash
#!/bin/bash
# Launch multi-drone simulation with AirSim

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PX4_DIR="$REPO_ROOT/external/PX4-Autopilot"
MICRO_XRCE_AGENT="$REPO_ROOT/external/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent"
WS_ROS2="$REPO_ROOT/ws_ros2"

echo -e "${GREEN}=== AirSim + PX4 + ROS2 Launcher ===${NC}"

# Instructions for manual AirSim startup
echo -e "${YELLOW}Please start AirSim manually:${NC}"
echo "  1. Run your AirSim environment (e.g., ~/AirSimEnvironments/Blocks/LinuxBlocks.sh)"
echo "  2. Wait for Unreal Engine to fully load"
echo "  3. Press ENTER when ready..."
read

# Terminal 1: MicroXRCE Agent
echo -e "${GREEN}Starting MicroXRCE Agent...${NC}"
gnome-terminal -- bash -c "
  echo 'MicroXRCE Agent on UDP 8888';
  $MICRO_XRCE_AGENT udp4 -p 8888;
  read
" &

sleep 2

# Terminal 2: PX4 SITL
echo -e "${GREEN}Starting PX4 SITL (will connect to AirSim)...${NC}"
gnome-terminal -- bash -c "
  cd $PX4_DIR;
  echo 'PX4 SITL - Connecting to AirSim on TCP 4560';
  ENABLE_LOCKSTEP_SCHEDULER=yes PX4_SIM_MODEL=none ./build/px4_sitl_default/bin/px4;
  read
" &

sleep 5

# Terminal 3: AirSim ROS Bridge
echo -e "${GREEN}Starting AirSim ROS Bridge...${NC}"
gnome-terminal -- bash -c "
  source /opt/ros/humble/setup.bash;
  source $WS_ROS2/install/setup.bash;
  echo 'AirSim ROS Bridge - Camera topics';
  ros2 run airsim_ros_pkgs airsim_node --ros-args \
    -p host_ip:=localhost \
    -r /airsim_node/Ally/front_center/Scene:=/camera/image \
    -r /airsim_node/Ally/front_center/camera_info:=/camera/camera_info;
  read
" &

sleep 3

# Terminal 4: Detection Node
echo -e "${GREEN}Starting Detection Node...${NC}"
gnome-terminal -- bash -c "
  source /opt/ros/humble/setup.bash;
  source $WS_ROS2/install/setup.bash;
  source $WS_ROS2/venv/bin/activate;
  echo 'Detection Node - YOLOv11n';
  ros2 run halcon1_detection detection_node;
  read
" &

# Terminal 5: Tracking Node
echo -e "${GREEN}Starting Tracking Node...${NC}"
gnome-terminal -- bash -c "
  source /opt/ros/humble/setup.bash;
  source $WS_ROS2/install/setup.bash;
  echo 'Tracking Node - Coordinate Transform';
  ros2 run halcon1_tracking tracking_node;
  read
" &

# Terminal 6: Guidance Node
echo -e "${GREEN}Starting Guidance Node...${NC}"
gnome-terminal -- bash -c "
  source /opt/ros/humble/setup.bash;
  source $WS_ROS2/install/setup.bash;
  echo 'Guidance Node - Kalman Filter + ProNav';
  ros2 run halcon1_guidance guidance_node;
  read
" &

echo -e "${GREEN}All nodes launched!${NC}"
echo -e "${YELLOW}Use QGroundControl to arm and takeoff the drone.${NC}"
```

Make executable:
```bash
chmod +x scripts/launch_airsim.sh
```

#### Step 8: Validation Testing

**Test Scenario**: Detect and intercept a second drone in AirSim

1. Modify `settings.json` to add enemy drone
2. Launch full pipeline with `scripts/launch_airsim.sh`
3. Arm and takeoff both drones via QGroundControl
4. Position enemy drone in front of ally camera view
5. Verify detection → tracking → guidance chain

**Success Metrics**:
- ✅ Camera images at 30+ Hz
- ✅ YOLO detections when enemy visible
- ✅ Tracking publishes world coordinates
- ✅ Guidance sends intercept commands
- ✅ PX4 executes commands in AirSim

### Deliverables

1. ✅ `config/airsim/settings.json` - PX4Multirotor configuration
2. ✅ `scripts/launch_airsim.sh` - Automated launch script
3. ✅ `docs/AIRSIM_SETUP.md` - Detailed installation and setup guide
4. ✅ Updated `README.md` - Document AirSim as alternative to Gazebo
5. ✅ Updated `TODO.md` - Mark Phase 1 complete

---

## Phase 2: Advanced Navigation

**Goal**: Integrate depth estimation, 3D mapping, and path planning from monocular-slam-drone.

**Status**: Planned after Phase 1 completion.

### New Modules (from monocular-slam-drone)

1. **Depth Estimation Module**
   - Port Depth Anything V2 from ROS1 → ROS2
   - Input: `/camera/image`
   - Output: `/depth/map`

2. **3D Mapping Module**
   - Port VoxArray 3D occupancy grid
   - Input: `/depth/map` + drone pose
   - Output: `/occupancy/occupied`, `/occupancy/empty`

3. **Path Planning Module**
   - Port A* 3D navigation
   - Input: current pose, goal pose, occupancy grid
   - Output: `/navigation/planned_path`

4. **Integration with Guidance**
   - Modify guidance to respect obstacle-free paths
   - Combine interception with collision avoidance

### Implementation Steps (Deferred)

1. Create `halcon1_depth_estimation` package (ROS2)
2. Create `halcon1_mapping` package (ROS2)
3. Create `halcon1_navigation` package (ROS2)
4. Integrate with existing guidance module
5. Test in complex AirSim environments (buildings, trees)

---

## Summary

### Current State
- ✅ Gazebo + PX4 + ROS2 working
- ✅ YOLO detection implemented
- ✅ Coordinate tracking implemented
- ✅ Kalman Filter + ProNav guidance implemented

### Phase 1 Goal
- 🎯 Add AirSim simulation support
- 🎯 Maintain Gazebo compatibility
- 🎯 No changes to Halcon1 ROS2 nodes
- 🎯 Prepare for real hardware deployment

### Phase 2 Goal (Future)
- 🔮 Depth estimation (monocular camera)
- 🔮 3D occupancy mapping
- 🔮 A* path planning
- 🔮 Obstacle avoidance during interception

### Key Principles
1. **Simulator-agnostic architecture**: Halcon1 nodes don't know about Gazebo or AirSim
2. **PX4-centric**: Always use PX4 as flight controller (even in simulation)
3. **Standard ROS2 topics**: Use standard message types for portability
4. **Minimal dependencies**: Easy transition from simulation to real hardware

---

## References

- [PX4 Documentation](https://docs.px4.io/)
- [AirSim Documentation](https://microsoft.github.io/AirSim/)
- [ROS2 Humble Documentation](https://docs.ros.org/en/humble/)
- [uXRCE-DDS Guide](https://docs.px4.io/main/en/middleware/uxrce_dds.html)
- [MAVLink Protocol](https://mavlink.io/en/)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Authors**: Halcon Team
