# Halcon1 Algorithms

## Overview

Halcon1's detection-tracking-guidance pipeline processes visual input into drone control commands through three stages:

1. **Detection** - YOLOv11n identifies enemy drone in camera frame
2. **Tracking** - Pinhole camera model + depth estimation transforms 2D pixels → 3D world coordinates
3. **Guidance** - Kalman Filter + Proportional Navigation generates interception trajectory

---

## Stage 1: Detection

**Algorithm:** YOLOv11n (Ultralytics)

**Input:** Camera image (BGR, 640x480 or 1280x960)

**Output:** Bounding box `(x, y, width, height)` in pixel coordinates

### Implementation

**File:** `src/ros2/modules/detection/detection/detection_algorithm.py`

**Model configuration:** `src/ros2/modules/detection/detection/config.yaml`

```yaml
# Default model: yolo11n.pt
selected_model: 'yolo11n_base'

models:
  yolo11n_base:
    name: 'yolo11n.pt'
    confidence_threshold: 0.5
    nms_threshold: 0.45
    target_classes: null  # All classes
```

### Detection Flow

1. **Load model** - Downloads `yolo11n.pt` on first run (6 MB)
2. **Run inference** - `self.model(image, conf=0.5, verbose=False)`
3. **Filter results** - Apply confidence threshold and target classes
4. **Temporal tracking** - Prefer detections close to previous frame (max 200px distance)
5. **Select best** - Closest to previous OR highest confidence

### Temporal Consistency

To maintain tracking lock on the same enemy drone:

```python
# Prefer detection closest to previous frame's position
if self.last_detection_box is not None:
    min_distance = float('inf')
    for box in drone_boxes:
        distance = box_center_distance(box, self.last_detection_box)
        if distance < min_distance:
            min_distance = distance
            best_idx = i

    # Reset if target moved too far (200px threshold)
    if min_distance > 200:
        self.last_detection_box = None
```

**Key parameters:**
- `confidence_threshold`: 0.5 (50%)
- `max_distance_threshold`: 200 pixels (temporal consistency)

### Debug Visualization

When launched with `--debug`, publishes annotated image to `/debug/ally/detection_image`:
- Green box (3px) = Primary detection
- Cyan box (2px) = Secondary detections
- White text = Class + confidence
- Yellow overlay = Model info + detection count

---

## Stage 2: Tracking

**Algorithm:** Pinhole camera model + similarity-based depth estimation

**Input:**
- Bounding box from detection
- Camera intrinsics (fx, fy, cx, cy)
- Friendly drone pose + orientation (from PX4)

**Output:** Enemy position `(x, y, z)` in ENU world coordinates

### Implementation

**File:** `src/ros2/modules/tracking/tracking/camera_transform.py`

### Coordinate Frames

1. **Camera pixel frame** - Origin: top-left, X: right, Y: down
2. **Optical frame** - Origin: optical center, X: right, Y: down, Z: forward
3. **ROS camera_link** - X: forward, Y: left, Z: up
4. **Body frame (FLU)** - Forward-Left-Up (same as camera_link)
5. **World frame (ENU)** - East-North-Up

### Depth Estimation

Uses **triangle similarity** from known enemy drone dimensions:

```python
enemy_drone_width = 0.5   # meters (configurable)
enemy_drone_height = 0.2  # meters (configurable)

# From bounding box width
z_width = (enemy_drone_width * fx) / bbox_width_pixels

# From bounding box height
z_height = (enemy_drone_height * fy) / bbox_height_pixels

# Average both estimates
depth = (z_width + z_height) / 2
```

**Limitations:**
- Requires known enemy dimensions
- Accuracy degrades with distance (>50m)
- Assumes rectangular aspect ratio

### Pinhole Camera Model

Convert pixel `(u, v)` to 3D camera coordinates:

```python
# Bounding box center
u = detection.x + detection.width / 2
v = detection.y + detection.height / 2

# Pinhole projection (optical frame)
offset_right = (u - cx) * depth / fx
offset_down = (v - cy) * depth / fy
distance_forward = depth

# Convert to ROS camera frame (X=forward, Y=left, Z=up)
camera_x = distance_forward
camera_y = -offset_right
camera_z = -offset_down
```

### Body-to-World Transformation

```python
# Camera frame = Body frame (FLU) for forward-facing camera
enemy_body = np.array([camera_x, camera_y, camera_z])

# Rotate from body FLU to world ENU using friendly drone's orientation
rotation_matrix = quaternion_to_rotation_matrix(friendly_orientation)
enemy_world_relative = rotation_matrix @ enemy_body

# Translate by friendly drone's world position
enemy_world = friendly_position + enemy_world_relative
```

**ROS2 Topic:** `/enemy/pose` (geometry_msgs/PoseStamped)

---

## Stage 3: Guidance

**Algorithms:** Kalman Filter (state estimation) + Proportional Navigation (guidance law)

**Input:**
- Enemy position measurements (from tracking)
- Friendly position + velocity (from PX4)

**Output:** Acceleration command `(ax, ay, az)` in NED frame

### Implementation

**Files:**
- `src/lib/algorithms/algorithms/kalman_filter.py`
- `src/lib/algorithms/algorithms/pro_nav.py`
- `src/ros2/modules/guidance/guidance/state_manager.py`

### Kalman Filter

**Purpose:** Estimate enemy state (position + velocity) from noisy position measurements.

**State vector:** `[x, y, z, vx, vy, vz, ax, ay, az]` (9D)

**Model:** Constant acceleration

**State transition:**
```python
# Position update
x = x + vx*dt + 0.5*ax*dt²

# Velocity update
vx = vx + ax*dt

# Acceleration (assumed constant between updates)
ax = ax
```

**Measurement:** Position only `[x, y, z]` (from tracking)

**Parameters:**
- `process_noise`: 0.1 (default, represents wind/turbulence)
- `sigma_pos`: 0.5 m (position measurement noise)
- Initial covariance: `P = I * 100`

**Usage:**
```python
# Predict step (runs at 50 Hz)
enemy_pos_est, enemy_vel_est = kalman.predict(current_time)

# Update step (when new measurement arrives, ~10 Hz)
kalman.update(enemy_pos_measured, current_time)
```

### Proportional Navigation

**Purpose:** Compute acceleration to intercept moving target.

**Formula:**
```
a_pronav = N * V_closing * ω_los * direction_perpendicular
```

Where:
- `N` = Navigation constant (typically 3-5)
- `V_closing` = Closing velocity along line-of-sight
- `ω_los` = Line-of-sight rotation rate

**Implementation:** Blends two strategies based on distance and speed:

1. **Directional acceleration** (when far OR slow):
   ```python
   a_dir = (enemy_pos - friendly_pos) / distance * max_acceleration
   ```
   Points directly at target to build speed.

2. **ProNav acceleration** (when close AND fast):
   ```python
   # LOS rate (perpendicular velocity)
   relative_velocity_perp = relative_velocity - (relative_velocity · los_unit) * los_unit
   los_rate = ||relative_velocity_perp|| / distance

   # ProNav command
   a_pronav = N * closing_velocity * los_rate * perpendicular_direction
   ```
   Nulls LOS rotation for collision course.

**Blending:**
```python
# Distance ratio: 0 when < threshold, 1 when > threshold + 100m
distance_ratio = clip((distance - 50) / 100, 0, 1)

# Speed ratio: 0 when slow, 1 when at max speed
speed_ratio = current_speed / max_velocity

# Directional weight: high when slow OR far
weight_dir = (1 - speed_ratio) * distance_ratio

# ProNav weight: high when fast AND close
weight_pronav = 1 - weight_dir

# Combined
a_final = weight_dir * a_dir + weight_pronav * a_pronav
```

**Parameters:**
- `navigation_constant`: 3.0 (higher = more aggressive)
- `max_acceleration`: 10.0 m/s² (safety limit)
- `max_velocity`: 20.0 m/s (safety limit)
- `directional_to_los_change_threshold`: 50.0 m (blend distance)
- `full_direction_acceleration`: 100.0 m (full directional distance)

**Interception termination:**
```python
# Stop accelerating when within 0.5m of target
if distance < 0.5:
    return zeros(3)
```

**ROS2 Topic:** `/fmu/in/trajectory_setpoint` (px4_msgs/TrajectorySetpoint) at 50 Hz

---

## Tuning Guide

### Detection

**Increase recall (find more drones):**
```yaml
confidence_threshold: 0.3  # Lower threshold (more false positives)
```

**Increase precision (fewer false positives):**
```yaml
confidence_threshold: 0.7  # Higher threshold (miss some drones)
```

**Reduce tracking jumps:**
```yaml
max_distance_threshold: 100  # Stricter temporal consistency
```

### Tracking

**If depth estimates are wrong:**
```python
# Adjust enemy drone dimensions in tracking_node.py
self.enemy_drone_width = 0.7   # Increase if underestimating depth
self.enemy_drone_height = 0.3
```

**Check camera calibration:**
```bash
ros2 topic echo /camera/camera_info
# Verify fx, fy, cx, cy are reasonable
```

### Guidance

**More aggressive interception:**
```python
KalmanFilterParameters(process_noise=0.05)  # Trust model more
ProportionalNavigationParameters(
    navigation_constant=5.0,      # Higher = sharper turns
    max_acceleration=15.0         # Allow higher G-forces
)
```

**Smoother, safer flight:**
```python
KalmanFilterParameters(process_noise=0.3)  # Trust measurements more
ProportionalNavigationParameters(
    navigation_constant=2.0,      # Lower = gentler turns
    max_acceleration=5.0,         # Limit G-forces
    max_velocity=10.0             # Lower speed limit
)
```

**Earlier ProNav engagement:**
```python
ProportionalNavigationParameters(
    directional_to_los_change_threshold=30.0,  # Start ProNav earlier
)
```

---

## See Also

- [Architecture](ARCHITECTURE.md) - System design and data flow
- [Development](DEVELOPMENT.md) - Testing and profiling
- [Simulation](SIMULATION.md) - Testing in simulators
