# Multi-Drone AirSim Setup - Ally vs Enemy

Complete guide for running the Halcon1 drone interception system with two drones in AirSim:
- **Ally** (PX4Multirotor) - Controlled by PX4, runs detection/tracking/guidance
- **Enemy** (SimpleFlight) - Controlled by AirSim API, acts as interception target

## AirSim Controls & Shortcuts

### Essential Keyboard Shortcuts
| Key | Function |
|-----|----------|
| **`\` (Backslash)** | **Cycle between Ally and Enemy drones** |
| `F1` | Show help menu with all shortcuts |
| `0-9` | Switch camera angles for current vehicle |
| `/` | Toggle sub-window (Ally's front camera) |
| `R` | Start/stop recording |
| `;` | Pause/unpause simulation |
| `T` | Toggle trajectory trace lines |

### Camera Movement
- **W/A/S/D**: Move camera
- **Q/E**: Move down/up
- **Mouse + Right-click**: Look around
- **Mouse Scroll**: Zoom

### View Both Drones
1. Start AirSim - you'll see Ally drone initially
2. Press **`\` (backslash)** to switch to Enemy drone view
3. Press **`\`** again to return to Ally
4. Use **`0`** for chase camera, **`1`** for FPV camera

**Tip**: Press `T` to enable trace lines so you can see both drone paths while following one.

## Quick Start

### Prerequisites

1. Complete single-drone AirSim setup: [QUICK_START_AIRSIM.md](QUICK_START_AIRSIM.md)
2. Enemy drone already added to `settings.json` (done in Phase 6)

### Launch Multi-Drone System

**Terminal 1: Start AirSim**
```bash
cd ~/AirSimEnvironments/Blocks/
./Blocks.sh
# Wait for environment to load - you should see BOTH drones
```

**Terminal 2: Launch Halcon1 Multi-Drone**
```bash
cd /home/eloy/Documents/Projects/drone-ws/halcon1-system

# Multi-drone mode (4 terminals)
./scripts/launch_airsim.sh --multi

# Multi-drone + Debug mode (6 terminals)
./scripts/launch_airsim.sh --multi --debug
```

This launches:
1. **MicroXRCE Agent** - PX4 ↔ ROS2 bridge
2. **PX4 SITL** - Ally drone flight controller
3. **AirSim Camera Bridge** - Camera from Ally drone
4. **Enemy Drone Controller** - Interactive enemy control (NEW)
5. **PX4 Debug Translator** - For RViz2 (if --debug)
6. **RViz2** - 3D visualization (if --debug)

## Operating Procedures

### Step-by-Step Flight

**1. Arm and Takeoff Ally Drone**

In PX4 SITL terminal:
```bash
pxh> commander arm
pxh> commander takeoff
```

Or use QGroundControl (auto-connects to UDP 14550).

Verify Ally is airborne and stable.

**2. Start Enemy Drone**

In "Enemy Drone Controller" terminal:
- Press `ENTER` when prompted
- Enemy will arm and takeoff automatically to 5 meters
- Menu will appear with movement options

**3. Select Enemy Movement Pattern**

```
Movement Patterns:
  1. Circular    - Fly in a circle
  2. Figure-8    - Fly in a figure-8 pattern
  3. Random      - Move to random positions
  4. Hover       - Hover at current position
  5. Land        - Land and disarm
  q. Quit        - Exit program
```

Choose pattern (e.g., `1` for circular), then optionally enter duration in seconds (or press ENTER for infinite).

**4. Launch Halcon1 Pipeline (Optional)**

In new terminals:
```bash
# Terminal: Detection
source ws_ros2/install/setup.bash
source ws_ros2/venv/bin/activate
ros2 run halcon1_detection detection_node

# Terminal: Tracking
source ws_ros2/install/setup.bash
ros2 run halcon1_tracking tracking_node

# Terminal: Guidance
source ws_ros2/install/setup.bash
ros2 run halcon1_guidance guidance_node
```

**5. Monitor System**

```bash
# Camera feed
ros2 topic hz /camera/image  # ~30 Hz expected

# Detection results (if enemy in view)
ros2 topic echo /enemy/detection --once

# Tracking results
ros2 topic echo /enemy/tracked --once

# Guidance commands
ros2 topic echo /interception/command --once

# Ally drone state
ros2 topic echo /fmu/out/vehicle_local_position --once
```

## Enemy Drone Control Details

### Movement Patterns

**1. Circular Movement**
- Enemy flies in a circle around spawn point
- Default radius: 8 meters
- Default speed: 3 m/s
- Good for: Consistent detection testing

**2. Figure-8 Movement**
- Enemy flies in a figure-8 (lemniscate) pattern
- Default radius: 8 meters
- Default speed: 3 m/s
- Good for: Complex trajectory tracking

**3. Random Movement**
- Enemy moves to random positions within ±15m bounds
- Hovers 2 seconds at each position
- Default speed: 3 m/s
- Good for: Unpredictable interception scenarios

**4. Hover**
- Enemy hovers at current position
- Good for: Stationary target practice

### Manual Enemy Control

You can also control the enemy drone manually:

```bash
# Interactive mode (launched automatically with --multi)
python3 scripts/control_enemy_airsim.py

# Auto mode with specific pattern
python3 scripts/control_enemy_airsim.py --auto 1 --duration 60  # Circular for 60s
python3 scripts/control_enemy_airsim.py --auto 2 --duration 0   # Figure-8 infinite
python3 scripts/control_enemy_airsim.py --auto 3 --duration 30  # Random for 30s

# Custom parameters
python3 scripts/control_enemy_airsim.py \
  --altitude 10 \      # 10 meters high
  --speed 5 \          # 5 m/s
  --radius 12 \        # 12 meter circle
  --auto 1 \           # Circular pattern
  --duration 120       # 2 minutes
```

### Command-Line Options

```bash
--host IP          # AirSim host IP (default: 127.0.0.1)
--vehicle NAME     # Vehicle name (default: Enemy)
--altitude METERS  # Flight altitude (default: 5.0)
--speed M/S        # Flight speed (default: 3.0)
--radius METERS    # Circle/Figure-8 radius (default: 8.0)
--auto PATTERN     # Auto pattern: 1=Circular, 2=Figure-8, 3=Random, 4=Hover
--duration SECONDS # Duration (default: 0=infinite)
```

## Configuration

### Drone Spawn Positions

Edit `~/Documents/AirSim/settings.json`:

```json
"Vehicles": {
  "Ally": {
    "VehicleType": "PX4Multirotor",
    "X": 0, "Y": 0, "Z": 0,  // Origin
    ...
  },
  "Enemy": {
    "VehicleType": "SimpleFlight",
    "X": 10, "Y": 0, "Z": 0,  // 10m in front of Ally
    "Yaw": 180               // Facing Ally
  }
}
```

**Position Guidelines:**
- Place Enemy in front of Ally camera (positive X)
- Keep 5-15 meters apart for good detection
- Altitude (Z): 0 = ground level (both spawn on ground)
- Yaw: 180° makes Enemy face Ally

### Camera Configuration

Ally's camera is already configured for detection:
- Resolution: 640×480
- FOV: 60°
- Position: 0.3m forward from drone center
- Facing: Straight ahead

Enemy should be within this FOV when Ally is airborne.

## Visualization

### RViz2 (Debug Mode Only)

If launched with `--debug`:

**Setup:**
1. Fixed Frame: `world`
2. Add → Pose → `/debug/ally/pose` (Green axis = Ally position)
3. Add → Path → `/debug/ally/path` (Flight trajectory)
4. Add → Image → `/camera/image` (Camera view)

**What you'll see:**
- Green axes showing Ally drone position
- Path showing Ally's flight history
- Camera image showing what Ally sees (including Enemy if in view)

### Camera View (Without Debug Mode)

```bash
ros2 run rqt_image_view rqt_image_view
# Select /camera/image
```

You should see the Enemy drone in the image when it's in front of Ally.

## Troubleshooting

### Enemy Drone Not Visible in AirSim

**Problem:** Only see Ally drone, Enemy is missing

**Solutions:**
1. Check settings.json has Enemy vehicle:
   ```bash
   cat ~/Documents/AirSim/settings.json | grep -A3 "Enemy"
   ```
2. Restart AirSim after editing settings.json
3. Check spawn position - Enemy might be behind or too far
4. In AirSim window, press `BACKSLASH` (\) to cycle between drones

### Enemy Control Script Fails

**Problem:** `control_enemy_airsim.py` shows connection error

**Solutions:**
1. Verify AirSim is running and loaded
2. Check AirSim Python package:
   ```bash
   python3 -c "import airsim; print('OK')"
   ```
3. Check Enemy vehicle exists in settings.json
4. Try manual connection test:
   ```python
   import airsim
   client = airsim.MultirotorClient()
   client.confirmConnection()
   client.enableApiControl(True, "Enemy")
   ```

### Enemy Drone Falls After Takeoff

**Problem:** Enemy arms, takes off briefly, then crashes

**Solutions:**
1. **SimpleFlight doesn't need LockStep** - This is normal for SimpleFlight
2. Use slower speed: `--speed 2` instead of `--speed 3`
3. Increase altitude gradually: Start with `--altitude 3`, then higher
4. Check AirSim physics settings (shouldn't need changes for SimpleFlight)

### No Detections Appearing

**Problem:** Enemy flying, but no `/enemy/detection` messages

**Solutions:**
1. **Check Enemy is in camera view:**
   ```bash
   ros2 run rqt_image_view rqt_image_view
   # Select /camera/image - do you see Enemy drone?
   ```

2. **Position Enemy in front of Ally:**
   - Ally faces positive X direction
   - Enemy should have positive X spawn (e.g., X: 10)
   - After takeoff, use Circular pattern to move Enemy in front

3. **Check detection node:**
   ```bash
   ros2 node list | grep detection
   ros2 topic list | grep detection
   ```

4. **Verify YOLO model loaded:**
   - Look for "Model loaded" in detection node terminal
   - Should see "YOLOv11n" message

### Ally Drone Not Responding to Guidance

**Problem:** Detection and tracking work, but Ally doesn't move toward Enemy

**Solutions:**
1. **Check guidance node is running:**
   ```bash
   ros2 node list | grep guidance
   ```

2. **Verify offboard mode enabled:**
   ```bash
   # In PX4 console:
   pxh> commander mode offboard
   ```

3. **Check trajectory setpoint topic:**
   ```bash
   ros2 topic echo /fmu/in/trajectory_setpoint --once
   ```
   Should show acceleration commands

4. **Monitor interception commands:**
   ```bash
   ros2 topic echo /interception/command --once
   ```

## Testing Scenarios

### Scenario 1: Stationary Target Interception
1. Ally takeoff → hover at 5m
2. Enemy takeoff → hover (pattern 4)
3. Launch detection + tracking + guidance
4. Ally should move toward Enemy

### Scenario 2: Moving Target Interception
1. Ally takeoff → hover at 5m
2. Enemy circular movement (pattern 1)
3. Launch full pipeline
4. Ally should predict and intercept

### Scenario 3: Evasive Target
1. Ally takeoff → enable offboard mode
2. Enemy random movement (pattern 3)
3. Launch full pipeline
4. Test guidance prediction

## Performance Tips

### For Smooth Simulation

1. **Lower graphics quality** in AirSim:
   - Press `~` (tilde key)
   - Type: `r.ScreenPercentage 70`
   - Type: `sg.ViewDistanceScale 0.5`

2. **Use Blocks environment** (fastest):
   - Smallest size (~400MB)
   - Simple geometry
   - Good performance

3. **Close RViz2** if not needed:
   - Only use `--debug` when visualizing
   - Camera feed alone is lighter

4. **Reduce enemy speed**:
   - `--speed 2` instead of `--speed 3`
   - Smoother physics simulation

## Advanced Usage

### Custom Waypoint Mission for Enemy

Create a Python script:

```python
#!/usr/bin/env python3
import airsim

client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True, "Enemy")

# Arm and takeoff
client.armDisarm(True, "Enemy")
client.takeoffAsync(vehicle_name="Enemy").join()

# Waypoints (NED coordinates)
waypoints = [
    (10, 5, -5),   # 10m forward, 5m right, 5m up
    (15, -5, -5),  # 15m forward, 5m left, 5m up
    (5, 0, -3),    # 5m forward, centered, 3m up
]

for x, y, z in waypoints:
    client.moveToPositionAsync(x, y, z, velocity=3,
                                vehicle_name="Enemy").join()

# Land
client.landAsync(vehicle_name="Enemy").join()
client.armDisarm(False, "Enemy")
```

### Synchronized Multi-Drone Missions

Control both drones programmatically:

```python
# Ally via PX4 offboard (ROS2 topics)
ros2 topic pub /fmu/in/trajectory_setpoint ...

# Enemy via AirSim API
client.moveToPositionAsync(x, y, z, vehicle_name="Enemy")
```

## Next Steps

- **Tune detection parameters**: Adjust YOLO confidence threshold
- **Optimize tracking**: Improve coordinate transformation accuracy
- **Tune guidance**: Adjust Kalman Filter and ProNav gains
- **Record flights**: Enable AirSim recording in settings.json
- **Add 3rd drone**: More complex interception scenarios

## Related Documentation

- [AirSim Quick Start](QUICK_START_AIRSIM.md) - Single drone setup
- [AirSim Configuration](../config/airsim/README.md) - settings.json details
- [Halcon1 Pipeline](../README.md#pipeline-modules) - Detection, tracking, guidance
- [AirSim Python API](https://microsoft.github.io/AirSim/apis/) - Official docs

---

**Questions?** Check the [AirSim troubleshooting guide](../config/airsim/README.md#troubleshooting) or open an issue.
