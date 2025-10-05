# Reference Frame Conventions

## Overview

This document describes all coordinate reference frames used in the Halcon1 drone tracking system and how they are transformed throughout the software stack.

---

## Reference Frames Summary

### 1. **PX4 Autopilot Frames**

#### World Frame: **NED (North-East-Down)**
- **+X**: North
- **+Y**: East
- **+Z**: Down (into the ground)
- Used by: PX4 autopilot, vehicle odometry messages

#### Body Frame: **FRD (Forward-Right-Down)**
- **+X**: Forward (drone nose direction)
- **+Y**: Right (starboard)
- **+Z**: Down (through drone belly)
- Used by: PX4 attitude representation

#### Quaternion Order: **[w, x, y, z]** (Hamilton convention)

---

### 2. **ROS2 Frames (REP-103 Standard)**

#### World Frame: **ENU (East-North-Up)**
- **+X**: East
- **+Y**: North
- **+Z**: Up (away from ground)
- Used by: All ROS2 nodes, visualization (RViz)

#### Body Frame: **FLU (Forward-Left-Up)**
- **+X**: Forward (drone nose direction)
- **+Y**: Left (port side)
- **+Z**: Up (through drone top)
- Used by: ROS2 tf frames, geometry messages

#### Quaternion Order: **[x, y, z, w]** (JPL convention, used by scipy)

---

### 3. **Gazebo Simulator Frames**

#### World Frame: **ENU (East-North-Up)**
- **+X**: East
- **+Y**: North
- **+Z**: Up
- Matches ROS2 convention

#### Model Body Frame: **FLU (Forward-Left-Up)**
- Same as ROS2 body frame
- `PX4_GZ_MODEL_POSE` parameter uses this convention

**Important:** When `PX4_GZ_MODEL_POSE` sets `yaw=0`, the drone faces **East** (+X in ENU). After PX4 interprets this as NED, it becomes **90° yaw** (facing +Y in NED, which is East).

---

### 4. **Camera Frames**

#### Optical Frame (OpenCV/Pinhole Camera Convention)
- **+X**: Right (image horizontal →)
- **+Y**: Down (image vertical ↓)
- **+Z**: Forward (optical axis, into scene)
- Used by: Raw pinhole camera projection math

#### ROS Camera Link Frame
- **+X**: Forward (optical axis)
- **+Y**: Left
- **+Z**: Up
- Used by: ROS camera_info, sensor_msgs

**Note:** In our system, the camera is mounted aligned with the drone body, so ROS camera_link frame = FLU body frame (identity transform).

---

## Transformation Pipeline

### 1. **PX4 → ROS2 Transformation**
**Location:** `utils/coordinate_transform.py`

#### Position: `ned_to_enu_local_frame()`
Transforms position vectors from NED to ENU:
```
ENU.x = NED.y  (East  = NED's East)
ENU.y = NED.x  (North = NED's North)
ENU.z = -NED.z (Up    = -Down)
```

#### Orientation: `px4_to_ros_orientation()`
Transforms quaternions from FRD-to-NED to FLU-to-ENU:
```
q_ros = NED_ENU_Q * q_px4 * AIRCRAFT_BASELINK_Q
```
Where:
- `NED_ENU_Q = euler(π, 0, π/2)`: World frame transformation (NED↔ENU)
- `AIRCRAFT_BASELINK_Q = euler(π, 0, 0)`: Body frame transformation (FRD↔FLU)

**Critical:** PX4 quaternions arrive in `[w,x,y,z]` order and must be reordered to `[x,y,z,w]` before transformation.

---

### 2. **Camera → World Transformation**
**Location:** `tracking/camera_transform.py`

Transforms enemy drone detections from camera pixels to world coordinates:

#### Step 1: Pixel → Optical Frame
Pinhole camera model projects 2D bounding box to 3D position in optical frame:
```
offset_right = (u - cx) * depth / fx
offset_down  = (v - cy) * depth / fy
position_optical = [depth, offset_right, offset_down]  # [Z, X, Y]
```

#### Step 2: Optical Frame → ROS Camera Frame
Convert from OpenCV convention to ROS convention:
```
camera.x =  optical.z  (forward)
camera.y = -optical.x  (left = -right)
camera.z = -optical.y  (up = -down)
```

#### Step 3: Camera Frame → Body Frame (FLU)
**Identity transformation** - camera is aligned with drone body:
```
body_flu = camera_frame  # No transformation needed
```

#### Step 4: Body Frame (FLU) → World Frame (ENU)
Rotate relative position by drone orientation quaternion:
```
R = quaternion_to_rotation_matrix(friendly_orientation_enu)
position_world_relative = R @ position_body_flu
```
The quaternion represents the FLU-to-ENU rotation (already converted from PX4).

#### Step 5: Relative → Absolute Position
Add friendly drone's absolute position:
```
enemy_position_world = friendly_position_enu + position_world_relative
```

---

### 3. **Tracking Node Integration**
**Location:** `tracking/tracking_node.py`

Receives PX4 odometry and converts to ROS2 for camera transformations:

```python
# Transform position from NED to ENU
self.friendly_pose = CoordinateTransform.ned_to_enu_local_frame(msg.position)

# Reorder PX4 quaternion from [w,x,y,z] to [x,y,z,w]
q_px4_wxyz = list(msg.q)
q_px4_xyzw = [q_px4_wxyz[1], q_px4_wxyz[2], q_px4_wxyz[3], q_px4_wxyz[0]]

# Transform orientation from PX4 (FRD-to-NED) to ROS2 (FLU-to-ENU)
self.friendly_orientation = CoordinateTransform.px4_to_ros_orientation(q_px4_xyzw)
```

These transformed values are then used in camera-to-world coordinate transformation.

---

### 4. **Debug Visualization**
**Location:** `adversarial/px4_debug_translator.py`

Converts PX4 messages to ROS2 standard messages for RViz visualization:

#### Gazebo Offset Handling
Since each PX4 instance has its own local origin, we need to apply the Gazebo spawn offset:

```python
# Parameters come in Gazebo ENU coordinates
enemy_offset_enu = [enemy_offset_x, enemy_offset_y, enemy_offset_z]

# Convert to NED for internal processing
enemy_offset_ned = [
    enemy_offset_enu_y,   # North = ENU Y
    enemy_offset_enu_x,   # East = ENU X
    -enemy_offset_enu_z   # Down = -ENU Z
]

# Add offset in NED space, then convert to ENU
global_ned_pos = msg.position + offset_ned
enu_pos = CoordinateTransform.ned_to_enu_local_frame(global_ned_pos)
```
**NOTE:** This is technically not necessary as the gazebo coordinates are already in ENU and ally drone is always at (0,0,0) so one could: enu_pos = msg.pos + enemy_offset_enu. However, we explicitly add the transformation to show that it has been taken into account. (this is minimal overhead and only in debug mode)
  
This creates a unified global reference frame for visualization where both drones are visible with correct relative positions.

---

## Why Multiple Frames?

### **PX4 uses NED/FRD** because:
- Aviation heritage: NED aligns with traditional navigation (North-based heading)
- Sensor conventions: Many IMUs/GPS output in NED
- Aerodynamic reference: FRD matches aircraft body-fixed axes

### **ROS2 uses ENU/FLU** because:
- Mathematical convenience: Z-up is intuitive for 3D graphics and robotics
- Standard in robotics: REP-103 specifies ENU for consistency across ROS packages
- Visualization: RViz and most 3D tools expect Z-up

### **Gazebo uses ENU/FLU** because:
- Matches ROS2 convention for seamless integration
- Standard in simulation: Most physics engines use Z-up

---

## Common Pitfalls Avoided

### 1. **Quaternion Ordering**
PX4 uses `[w,x,y,z]` while scipy/numpy use `[x,y,z,w]`. Always reorder before mathematical operations.

### 2. **Incomplete Frame Transformations**
Must transform BOTH world frame (NED↔ENU) AND body frame (FRD↔FLU). Doing only one causes 180° errors.

### 3. **Offset Frame Confusion**
Gazebo spawn offsets are in ENU. Must convert to NED before adding to PX4 odometry, then convert back to ENU for ROS2.

### 4. **Camera Frame Alignment**
Even though camera and body frames align (both FLU), the intermediate optical frame requires explicit conversion from OpenCV convention.

---

## Verification

The implementation has been verified against:
1. **PX4 Official Library**: `px4_ros_com/frame_transforms` (C++)
2. **Simulation Testing**: Gazebo spawn positions match RViz visualization
3. **Mathematical Correctness**: All transformations preserve vector magnitudes and orthogonality

---

## References

- [ROS REP-103: Standard Units of Measure and Coordinate Conventions](https://www.ros.org/reps/rep-0103.html)
- [PX4 Coordinate Systems Documentation](https://docs.px4.io/main/en/ros/external_position_estimation.html#reference-frames-and-ros)
- [PX4 px4_ros_com frame_transforms Library](https://github.com/PX4/px4_ros_com/blob/main/include/px4_ros_com/frame_transforms.h)
- [OpenCV Camera Calibration](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)
