# Multi-Drone PX4 Simulation

Simplified multi-drone simulation using PX4's official approach.

## Quick Start

### Option 1: Using Bash Scripts

```bash
# Launch 2 drones (1 regular, 1 with camera)
./scripts/simple_two_drones.sh

# Launch N drones (default 2)
./scripts/launch_multi_drone.sh 3  # for 3 drones
```

### Option 2: Using ROS2 Launch

```bash
# Build the package first
cd ws_ros2
colcon build --packages-select multi_drone_sim
source install/setup.bash

# Launch 2 drones
ros2 launch multi_drone_sim two_drones.launch.py

# Launch 3 drones
ros2 launch multi_drone_sim multi_drone.launch.py
```

## Architecture

- **No custom world files needed** - PX4 handles spawning
- **Automatic port management** - Each instance gets unique ports
- **Built-in namespacing** - ROS2 topics automatically namespaced
  - Instance 0: `/fmu/out/*`, `/fmu/in/*`
  - Instance 1: `/px4_1/fmu/out/*`, `/px4_1/fmu/in/*`
  - Instance 2: `/px4_2/fmu/out/*`, `/px4_2/fmu/in/*`

## Key Environment Variables

- `PX4_SYS_AUTOSTART=4001` - X500 quadrotor
- `PX4_SIM_MODEL` - Model to spawn (gz_x500, gz_x500_mono_cam)
- `PX4_GZ_STANDALONE=1` - Connect to existing Gazebo (for instances 1+)
- `PX4_GZ_MODEL_POSE="x,y"` - Spawn position

## Testing Commands

```bash
# List all topics
ros2 topic list

# Echo drone states
ros2 topic echo /fmu/out/vehicle_status
ros2 topic echo /px4_1/fmu/out/vehicle_status

# Check camera topics (for drone with camera)
ros2 topic list | grep camera
```

## Sending Commands

When sending commands to specific drones:
- Instance 0: `target_system = 1`
- Instance 1: `target_system = 2`
- Instance N: `target_system = N + 1`