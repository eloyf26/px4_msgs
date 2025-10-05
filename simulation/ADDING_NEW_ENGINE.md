# Adding a New Simulation Engine

This guide shows you exactly how to add support for a new simulator (Isaac Sim, Webots, FlightGear, etc.) to Halcon1.

## Quick Start

**Time required**: ~1-2 hours for a basic implementation

1. Copy the template
2. Implement 6 required methods
3. Test with launch script
4. Done!

## Step-by-Step Guide

### Step 1: Create Directory Structure

```bash
cd simulation/
mkdir -p <your_sim>/{config,debug}
```

Example for Isaac Sim:
```bash
mkdir -p isaac/{config,debug}
```

### Step 2: Copy Template

```bash
cp TEMPLATE_ENGINE.py <your_sim>/engine.py
```

Example:
```bash
cp TEMPLATE_ENGINE.py isaac/engine.py
```

### Step 3: Implement Required Methods

Open `<your_sim>/engine.py` and search for `TODO`. You need to implement **6 required methods**:

#### 3.1 `get_name()` - Simple String

```python
def get_name(self) -> str:
    return "Isaac Sim"  # Your simulator name
```

#### 3.2 `validate_installation()` - Check if Installed

Check that your simulator is installed and configured:

```python
def validate_installation(self) -> Tuple[bool, str]:
    # Check simulator command exists
    import shutil
    if not shutil.which("isaacsim"):
        return False, "Isaac Sim not found. Install from: ..."

    # Check Python API available
    try:
        import omni.isaac.core
    except ImportError:
        return False, "Isaac Sim Python API not found"

    # Check ROS2 bridge built
    result = subprocess.run(
        ["ros2", "pkg", "prefix", "isaac_ros2_bridge"],
        capture_output=True
    )
    if result.returncode != 0:
        return False, "isaac_ros2_bridge not built. Run: ./setup.sh --isaac"

    return True, "Isaac Sim validated successfully"
```

#### 3.3 `launch_simulator()` - Start Physics Engine

Launch your simulator's GUI/headless process:

```python
def launch_simulator(self) -> bool:
    print(f"[{self.get_name()}] Launching simulator...")

    # Build command to launch simulator
    sim_cmd = [
        "/opt/isaac-sim/isaac-sim.sh",
        "--world", self.config.world,
        "--headless" if not self.config.debug else ""
    ]

    # Launch in new terminal window (inherited from base class)
    proc = self._launch_in_terminal(
        title="Isaac Sim",
        cmd=sim_cmd,
        color="blue"
    )

    if proc:
        self.processes.append(("simulator", proc))
        print(f"[{self.get_name()}] ✓ Simulator started")
        time.sleep(10)  # Wait for simulator to initialize
        return True
    else:
        print(f"[{self.get_name()}] ERROR: Failed to start simulator")
        return False
```

**Key points**:
- Use `self._launch_in_terminal()` to spawn GUI processes
- Append to `self.processes` to track for cleanup
- Wait for simulator to initialize before returning

#### 3.4 `launch_bridges()` - Start ROS2 Bridges

Launch bridges to convert simulator topics to Halcon1's expected topics:

```python
def launch_bridges(self) -> bool:
    print(f"[{self.get_name()}] Launching ROS2 bridges...")

    ws_setup = self.ws_ros2 / "install" / "setup.bash"

    # Camera bridge: /isaac/camera/rgb → /camera/image
    camera_cmd = [
        "bash", "-c",
        f"source /opt/ros/humble/setup.bash && "
        f"source {ws_setup} && "
        f"ros2 run isaac_camera_bridge camera_bridge"
    ]

    proc = self._launch_in_terminal(
        title="Isaac Camera Bridge",
        cmd=camera_cmd,
        color="green"
    )

    if proc:
        self.processes.append(("camera_bridge", proc))
        print(f"[{self.get_name()}] ✓ Camera bridge started")
        time.sleep(2)
        return True
    else:
        return False
```

**Required topics**:
- `/camera/image` (sensor_msgs/Image)
- `/camera/camera_info` (sensor_msgs/CameraInfo)

#### 3.5 `get_camera_topic()` - Camera Topic Name

Return the **final** topic name after bridge remapping:

```python
def get_camera_topic(self, drone_name: str = "Ally") -> str:
    return "/camera/image"  # Standard Halcon1 topic
```

#### 3.6 `get_px4_connection_config()` - MAVLink Config

Tell PX4 how to connect to your simulator:

```python
def get_px4_connection_config(self, instance_id: int) -> Dict:
    # TCP for lockstep mode (recommended)
    return {
        "protocol": "tcp",
        "port": 4560,
        "address": "localhost"
    }

    # OR UDP for faster mode
    # return {
    #     "protocol": "udp",
    #     "port": 14560 + instance_id,
    #     "address": "localhost"
    # }
```

**Recommendations**:
- Use **TCP + lockstep** for accurate physics simulation
- Use **UDP** only if your sim doesn't support lockstep

#### 3.7 `get_px4_env_vars()` - PX4 Environment Variables

Configure PX4 for your simulator:

```python
def get_px4_env_vars(self, drone_config: DroneConfig) -> Dict[str, str]:
    return {
        # Model: "none" if sim provides physics, else PX4 model name
        "PX4_SIM_MODEL": "none",

        # Quadcopter configuration
        "PX4_SYS_AUTOSTART": "4001",

        # Add simulator-specific vars
        "PX4_SIM_HOST": "localhost",  # For TCP
    }
```

### Step 4: Register Your Engine

At the bottom of your engine file:

```python
# Register with factory (used by launcher)
SimulationEngineFactory.register_engine("isaac", IsaacSimEngine)
#                                        ^^^^^^  ^^^^^^^^^^^^^^^
#                                        CLI name  Your class name
```

The CLI name is what users type:
```bash
./scripts/launch.sh --sim isaac
```

### Step 5: Update Launcher

Edit `simulation/common/launcher.py` to import your engine:

```python
# Line ~36, add your import
sys.path.insert(0, str(Path(__file__).parent.parent / "isaac"))
import engine as isaac_engine  # noqa
```

This automatically registers your engine when the launcher starts.

### Step 6: Test

```bash
# Test basic launch
./scripts/launch.sh --sim <your_sim>

# Test multi-drone mode
./scripts/launch.sh --sim <your_sim> --mode multi

# Test debug mode (RViz2)
./scripts/launch.sh --sim <your_sim> --debug
```

**Expected output**:
```
[Launcher] Using <Your Simulator> simulation engine
[Launcher] ✓ Installation validated successfully
[<Your Simulator>] Launching simulator...
[<Your Simulator>] ✓ Simulator started
[<Your Simulator>] Launching ROS2 bridges...
[<Your Simulator>] ✓ Camera bridge started
...
[Launcher] ✓ Halcon1 System Running
```

## Optional Enhancements

### Add Custom Worlds

Override `get_available_worlds()`:

```python
def get_available_worlds(self) -> List[str]:
    return ["default", "warehouse", "outdoor", "city"]

def validate_world(self, world_name: str) -> Tuple[bool, str]:
    world_path = self.config_dir / "worlds" / f"{world_name}.usd"
    if not world_path.exists():
        return False, f"World not found: {world_path}"
    return True, f"World '{world_name}' is available"
```

### Add Debug Visualization

Override `launch_debug_translator()`:

```python
def launch_debug_translator(self, drones: List[DroneConfig]) -> bool:
    # Launch ally visualizer (always)
    ws_setup = self.ws_ros2 / "install" / "setup.bash"

    ally_cmd = [
        "bash", "-c",
        f"source /opt/ros/humble/setup.bash && "
        f"source {ws_setup} && "
        f"ros2 run ally_visualizer ally_visualizer"
    ]

    proc = self._launch_in_terminal("Ally Visualizer", ally_cmd, "green")
    if proc:
        self.processes.append(("ally_visualizer", proc))
        print(f"[{self.get_name()}] ✓ Ally visualizer started")

    # TODO: Add enemy visualizer if multi-drone

    return True
```

### Add Custom Cleanup

Override `cleanup()`:

```python
def cleanup(self) -> bool:
    # ALWAYS call parent cleanup first
    success = super().cleanup()

    # Add simulator-specific cleanup
    try:
        # Kill any lingering simulator processes
        subprocess.run(["pkill", "-f", "isaac-sim"], timeout=5)

        # Reset configuration files if needed
        # ...
    except Exception as e:
        print(f"[{self.get_name()}] Cleanup error: {e}")
        success = False

    return success
```

### Add Feature Support

Override `supports_feature()`:

```python
def supports_feature(self, feature: str) -> bool:
    supported = {
        "rgb_camera",
        "depth_camera",
        "lidar",
        "segmentation",
        "gpu_acceleration",
        "photo_realistic",
        "headless",
        "rtx_rendering"
    }
    return feature in supported
```

## What You Get for Free

By inheriting from `SimulationEngineBase`, you automatically get:

### ✅ Terminal Management
- `self._detect_terminal()` - Finds gnome-terminal, xterm, konsole, terminator
- `self._launch_in_terminal(title, cmd, color, cwd)` - Launches processes in colored terminals

### ✅ Process Tracking
- `self.processes` - List of (name, process) tuples
- Automatic cleanup on Ctrl+C

### ✅ Common Paths
- `self.repo_root` - halcon1-system/
- `self.px4_dir` - external/PX4-Autopilot/
- `self.ws_ros2` - ws_ros2/

### ✅ Default Implementations
- `get_default_world()` → "default"
- `get_available_worlds()` → ["default"]
- `validate_world()` → Check in available worlds
- `get_world_launch_info()` → Basic info dict
- `get_microxrce_port()` → 8888 + instance_id
- `cleanup()` → Terminate all tracked processes

## Troubleshooting

### "Engine not found" when launching

**Problem**: `ValueError: Unknown simulation engine 'mysim'`

**Solution**: Make sure you:
1. Registered the engine: `SimulationEngineFactory.register_engine("mysim", MySimEngine)`
2. Imported in launcher.py: `import engine as mysim_engine`

### Processes don't appear in terminals

**Problem**: Processes launch but no terminal windows open

**Solution**:
1. Check if gnome-terminal is installed: `sudo apt install gnome-terminal`
2. Verify `self._launch_in_terminal()` returns a process
3. Check terminal detection with: `self._detect_terminal()`

### Camera feed not showing

**Problem**: `/camera/image` topic not published

**Solution**:
1. Check bridge is running: `ros2 node list | grep bridge`
2. Check bridge topics: `ros2 topic list | grep camera`
3. Verify simulator is publishing to source topic
4. Check remapping in bridge command

### PX4 won't connect

**Problem**: PX4 shows "Waiting for connection on port XXXX"

**Solution**:
1. Verify port matches: `get_px4_connection_config()` port = PX4 expected port
2. For TCP: Ensure simulator is listening BEFORE PX4 starts
3. For UDP: Check firewall isn't blocking port
4. Verify protocol (TCP vs UDP) matches simulator's mode

## Complete Example: Isaac Sim

See `simulation/isaac/` for a complete example implementation (coming soon).

## Summary Checklist

Before submitting your new engine:

- [ ] Implemented all 6 required methods
- [ ] Registered engine with factory
- [ ] Imported in launcher.py
- [ ] Tested single drone mode
- [ ] Tested multi-drone mode (if supported)
- [ ] Tested debug mode with RViz2
- [ ] Created README.md in `simulation/<your_sim>/`
- [ ] Documented installation steps
- [ ] Listed available worlds/environments
- [ ] Provided troubleshooting tips

## Getting Help

- Check existing engines: `simulation/gazebo/engine.py`, `simulation/airsim/engine.py`
- Read the base class: `simulation/common/base/engine_base.py`
- Review the interface: `simulation/common/interfaces/sim_engine.py`
- See the template: `simulation/TEMPLATE_ENGINE.py`

## Benefits of This Architecture

✅ **Only ~200 lines of code** - Most boilerplate is in the base class
✅ **Clear template** - Know exactly what to implement
✅ **Automatic terminal management** - No copy-paste utility code
✅ **Consistent interface** - All simulators work the same way
✅ **Easy testing** - Launch script works immediately

Happy simulating! 🚁
