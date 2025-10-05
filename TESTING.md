# Halcon1 Full Pipeline Testing Procedure

## Overview
This document describes how to test the complete Halcon1 pipeline with PX4 SITL, MicroXRCE Agent, and ROS2 integration.

## Detection Node Behavior
The detection node now fabricates realistic moving target detections:
- Oscillates in X: 320 ± 50 pixels (sine wave, 0.5 Hz)
- Oscillates in Y: 240 ± 30 pixels (cosine wave, 0.3 Hz)
- Constant confidence: 0.95

This simulates a moving enemy drone being tracked by the camera.

## 3-Terminal Testing Procedure

### Terminal 1: PX4 SITL
```bash
cd ~/drone_ws/PX4-Autopilot
make px4_sitl gz_x500
```
**Expected Output:**
- Gazebo launches with X500 quadcopter
- PX4 console shows "pxh>" prompt
- Vehicle initializes and arms successfully

### Terminal 2: MicroXRCE Agent
```bash
cd ~/drone_ws/Micro-XRCE-DDS-Agent/build
./MicroXRCEAgent udp4 -p 8888
```
**Expected Output:**
- Agent starts listening on UDP port 8888
- Shows connection when PX4 client connects
- Displays periodic keep-alive messages

### Terminal 3: ROS2 Halcon1 Pipeline
```bash
cd ~/drone_ws/ws_ros2
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch bringup pipeline.launch.py
```
**Expected Output:**
- All 4 nodes start successfully
- No error messages in launch output

### Terminal 4: Monitoring (Optional)
```bash
source ~/drone_ws/ws_ros2/install/setup.bash

# Check topic rates
ros2 topic hz /enemy/detection    # Should show ~10 Hz
ros2 topic hz /enemy/tracked      # Should show ~10 Hz

# Monitor data flow
ros2 topic echo /enemy/detection --once
ros2 topic echo /enemy/tracked --once
ros2 topic echo /enemy/predicted --once
ros2 topic echo /interception/command --once

# List all active topics
ros2 topic list
```

## Expected Data Flow

### /enemy/detection (10 Hz)
```
x: 320.0 + 50*sin(t*0.5)  # Moving target
y: 240.0 + 30*cos(t*0.3)  # Moving target
confidence: 0.95
```

### /enemy/tracked (10 Hz)
```
x: (detection.x / 100.0)  # Scaled to meters
y: (detection.y / 100.0)  # Scaled to meters
z: 10.0                   # Fixed altitude
vx: 1.0                   # Fixed velocity
vy: 0.0
vz: 0.0
```

### /enemy/predicted (10 Hz)
```
times: [1.0, 2.0, 3.0]
x: [tracked.x + vx*t, ...]  # Linear extrapolation
y: [tracked.y + vy*t, ...]
z: [tracked.z + vz*t, ...]
```

### /interception/command (10 Hz)
```
target_x: predicted.x[0]  # First predicted point
target_y: predicted.y[0]
target_z: predicted.z[0]
```

## Integration Verification

### 1. PX4 Topics Available
```bash
ros2 topic list | grep fmu
```
Should show PX4 topics like:
- /fmu/in/trajectory_setpoint
- /fmu/out/vehicle_odometry

### 2. Data Pipeline Working
```bash
# Check pipeline timing
ros2 run rqt_graph rqt_graph  # Visual node graph
ros2 topic hz /interception/command  # End-to-end rate
```

### 3. Moving Target Simulation
```bash
# Watch changing coordinates
ros2 topic echo /enemy/detection | head -20
```
You should see x,y coordinates changing over time in oscillating pattern.

## Success Criteria
- ✅ PX4 SITL launches and arms successfully
- ✅ MicroXRCE Agent connects to PX4
- ✅ All 4 ROS2 nodes start without errors
- ✅ Topics publish at expected rates (~10 Hz)
- ✅ Detection coordinates change over time (moving target)
- ✅ Data flows through all pipeline stages
- ✅ Interception commands generate target positions

## Troubleshooting

### PX4 Issues
- **Won't arm**: Check GPS lock, run `commander arm` in pxh console
- **Gazebo crashes**: Restart terminal, ensure no other Gazebo instances

### MicroXRCE Issues
- **Port busy**: Kill existing agents with `pkill MicroXRCEAgent`
- **No connection**: Check PX4 RTPS client settings

### ROS2 Issues
- **Build errors**: Run `colcon build --allow-overriding detection`
- **Topic not found**: Check node startup order, restart launch

This testing procedure validates the complete Halcon1 system integration without requiring real camera input or complex algorithms.