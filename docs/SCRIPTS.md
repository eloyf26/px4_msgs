# Halcon1 Scripts Documentation

## Overview

Halcon1 provides several utility scripts to streamline development, testing, and deployment workflows. This document describes **exactly** what each script does based on the actual implementation.

## Main Scripts

### setup.sh

**Purpose:** Complete system installation and configuration

**Location:** `./setup.sh`

**Usage:**
```bash
# Install for Gazebo only (fast, lightweight)
./setup.sh --gazebo

# Install for AirSim only (photo-realistic)
./setup.sh --airsim

# Install for both simulators
./setup.sh --full

# Validate existing installation
./setup.sh --validate

# Show help
./setup.sh --help
```

**Exact behavior:**
1. **Validates Python dependencies** - Checks for:
   - ultralytics, torch, torchvision
   - opencv-python, numpy, scipy, PyYAML
   - airsim, msgpack-rpc-python (if AirSim mode)
   - Offers to install missing packages interactively

2. **Initializes git submodules** - `git submodule update --init --recursive`

3. **Builds PX4-Autopilot** (if `--gazebo` or `--full`):
   - Runs PX4 toolchain setup
   - Builds with `make px4_sitl_default gz_x500_mono_cam`

4. **Builds Micro-XRCE-DDS-Agent**:
   - Creates build directory
   - Runs cmake and make

5. **Clones and builds ros_gz** (if `--gazebo` or `--full`):
   - Clones to `src/ros2/simulation/gazebo/bridges/ros_gz/`
   - Builds with colcon

6. **Installs AirSim packages** (if `--airsim` or `--full`):
   - Installs airsim via pip
   - Installs msgpack-rpc-python

7. **Builds ROS2 workspace**:
   - Sources ROS2 Humble
   - Runs `colcon build --symlink-install`

8. **Validates installation** (if `--validate`):
   - Runs `./scripts/validate.sh`

**Options:**
- `--gazebo`: Gazebo-only setup (default if no option given)
- `--airsim`: AirSim-only setup
- `--full`: Both Gazebo and AirSim
- `--validate`: Only run validation checks, don't install anything
- `--help`: Show usage information

**Time:** 15-25 minutes depending on options

---

### launch.sh

**Purpose:** Unified launcher wrapper (calls Python launcher)

**Location:** `./scripts/launch.sh`

**Exact behavior:**
1. **Pre-flight checks**:
   - Verifies python3 is installed
   - Verifies ROS2 Humble exists at `/opt/ros/humble/setup.bash`
   - Verifies workspace is built (`install/setup.bash` exists)
   - Verifies launcher script exists

2. **Sources environments**:
   - Sources `/opt/ros/humble/setup.bash`
   - Sources `install/setup.bash`

3. **Executes Python launcher**:
   - Runs `python3 src/ros2/simulation/common/launcher.py` with all arguments
   - Python launcher inherits the sourced ROS2 environment

**Usage:**
```bash
# Launch Gazebo (default)
./scripts/launch.sh --sim gazebo

# Launch AirSim
./scripts/launch.sh --sim airsim

# Multi-drone mode (ally + enemy)
./scripts/launch.sh --sim gazebo --mode multi

# With debug visualization
./scripts/launch.sh --sim gazebo --debug

# Show help
./scripts/launch.sh --help
```

**Parameters (handled by Python launcher):**

| Parameter | Options | Default | Description |
|-----------|---------|---------|-------------|
| `--sim, --simulator` | `gazebo`, `airsim` | `gazebo` | Simulator to use |
| `--mode` | `single`, `multi`, `hardware` | `single` | Simulation mode |
| `--debug` | (flag) | off | Enable debug visualizers (ally/enemy markers) |
| `-h, --help` | (flag) | - | Show help message |

**What the Python launcher does:**
1. Detects available terminal emulator (gnome-terminal, xterm, konsole, terminator)
2. Validates simulator installation via SimulationEngine interface
3. Launches simulator in separate terminal (Gazebo GUI or detects AirSim)
4. Launches PX4 SITL instance(s) in separate terminals
5. Launches Micro-XRCE-DDS Agent(s) in separate terminals
6. Launches simulator-specific ROS2 bridges in separate terminals
7. Launches Halcon1 pipeline (bringup) in separate terminal
8. Launches RViz2 in separate terminal
9. Launches debug visualizers if `--debug` (ally_visualizer, enemy_visualizer)
10. Launches enemy control if `--mode multi`
11. Handles Ctrl+C gracefully - terminates all spawned processes

**Terminal windows opened:**
- PX4 SITL (1 per drone)
- Micro-XRCE-DDS Agent (1 per drone)
- Simulator bridges (camera, etc.)
- Halcon1 Pipeline
- RViz2
- Debug visualizers (if --debug)
- Enemy control (if multi mode)

**Cleanup:** Press `Ctrl+C` in the original terminal to cleanly terminate all processes.

---

### validate.sh

**Purpose:** Validate Halcon1 installation and dependencies

**Location:** `./scripts/validate.sh`

**Usage:**
```bash
# Full validation
./scripts/validate.sh
```

**Exact behavior:**
Checks the following items and provides color-coded status:

**Core Dependencies:**
- ✓ ROS2 Humble installed (`/opt/ros/humble/setup.bash` exists)
- ✓ Python 3 installed (`python3` command available)
- ✓ pip3 installed (`pip3` command available)
- ✓ colcon build tools (`colcon` command available)

**PX4 SITL:**
- ✓ PX4 repository cloned (`external/PX4-Autopilot/` exists)
- ✓ PX4 SITL binary built (`external/PX4-Autopilot/build/px4_sitl_default/bin/px4` exists)
- ✓ MicroXRCE-DDS Agent built (`external/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent` exists)

**Gazebo Harmonic (optional):**
- ○ Gazebo Harmonic installed (`gz` command available)
- ○ ros_gz_interfaces built
- ○ ros_gz_bridge built
- ○ ros_gz_sim built

**AirSim (optional):**
- ○ AirSim Python package installed (`import airsim` works)
- ○ msgpack-rpc-python installed (`import msgpackrpc` works)

**ROS2 Workspace:**
- ✓ Workspace built (`install/setup.bash` exists)
- ✓ Core packages built (detection, tracking, guidance, etc.)

**Python Dependencies:**
- ✓ ultralytics installed
- ✓ torch installed
- ✓ opencv-python installed
- ✓ numpy installed
- ✓ scipy installed
- ✓ PyYAML installed

**Git Submodules:**
- ✓ PX4-Autopilot submodule initialized
- ✓ Micro-XRCE-DDS-Agent submodule initialized

**Output:**
- ✓ (green check) = Required item present
- ○ (yellow circle) = Optional item missing
- ✗ (red X) = Required item missing (shows fix command)

**Exit code:**
- `0` = All required dependencies present
- `1` = One or more required dependencies missing

---

### rebuild.sh

**Purpose:** Quick rebuild after code changes

**Location:** `./scripts/rebuild.sh`

**Usage:**
```bash
# Rebuild core packages only (default)
./scripts/rebuild.sh

# Rebuild specific packages
./scripts/rebuild.sh detection tracking guidance

# Clean rebuild (removes build/install/log first)
./scripts/rebuild.sh --clean

# Rebuild Gazebo packages
./scripts/rebuild.sh --gazebo

# Rebuild AirSim packages
./scripts/rebuild.sh --airsim

# Rebuild everything (Gazebo + AirSim + Core)
./scripts/rebuild.sh --all

# Combine options
./scripts/rebuild.sh --clean --all

# Show help
./scripts/rebuild.sh --help
```

**Exact behavior:**

1. **Validates workspace exists** - Checks for `install/setup.bash`

2. **Clean if requested** (with `--clean`):
   - Removes `build/`
   - Removes `install/`
   - Removes `log/`

3. **Sources ROS2**:
   - Sources `/opt/ros/humble/setup.bash`
   - Sets `GZ_VERSION=harmonic`

4. **If specific packages provided**:
   - Builds only those packages with `colcon build --packages-select`
   - Sources workspace after each package

5. **Otherwise, builds in dependency order**:

   **Always builds first:**
   - `px4_msgs` - PX4 message definitions

   **If `--gazebo` or `--all`:**
   - `ros_gz_interfaces`
   - `ros_gz_sim`
   - `ros_gz_bridge`
   - `ros_gz_image`
   - `ros_gz_sim_demos`
   - `ros_gz` (meta-package)

   **If `--core` or default:**
   - `msgs` - Halcon1 message definitions
   - `common_types`, `transforms`, `algorithms` - Shared libraries
   - `detection`, `tracking`, `guidance` - Main modules
   - `ally_visualizer` - Debug visualization
   - `bringup` - Launch files

   **If `--gazebo` or `--all`:**
   - `gazebo_enemy_control`
   - `gazebo_enemy_visualizer`

   **If `--airsim` or `--all`:**
   - `camera_bridge`
   - `airsim_enemy_control`
   - `airsim_enemy_visualizer`

6. **Sources workspace after each build step**

7. **Shows colorized build progress** with headers

**Options:**
- `--clean`: Remove build/install/log before rebuilding
- `--gazebo`: Rebuild Gazebo packages (ros_gz, gazebo_enemy_*)
- `--airsim`: Rebuild AirSim packages (camera_bridge, airsim_enemy_*)
- `--all`: Rebuild everything (Gazebo + AirSim + Core)
- `--help`: Show help message
- (package names): Rebuild specific packages only

**Output:**
- Colorized progress (green = success, yellow = in progress, red = error)
- Shows which packages are being built
- Final message to source workspace

---

### cleanup.sh

**Purpose:** Clean up all Halcon1-related processes

**Location:** `./scripts/cleanup.sh`

**Usage:**
```bash
# Kill all Halcon1-related processes
./scripts/cleanup.sh
```

**Exact behavior:**

Kills the following processes (in order):

1. **PX4 instances:**
   - Processes matching pattern `px4`

2. **MicroXRCE Agent:**
   - Processes matching pattern `MicroXRCEAgent`

3. **Gazebo processes:**
   - `gz sim`, `gz gui`, `gzserver`, `gzclient`
   - `ruby.*gz`, `ign gazebo`, `ignition`
   - Any process matching `gazebo` or `gz`

4. **AirSim/Unreal processes:**
   - `Blocks`, `CityEnviron`, `LandscapeMountains`
   - `AirSim`, `UE4`, `UnrealEngine`

5. **ROS2 bridge nodes:**
   - Gazebo: `ros2.*parameter_bridge`, `ros_gz_bridge`, `enemy_offboard_control`, `px4_debug_translator`
   - AirSim: `airsim_camera_bridge`, `airsim_viz_translator`, `control_enemy_airsim`

6. **Halcon1 pipeline nodes:**
   - `detection_node`, `tracking_node`, `guidance_node`

7. **Visualization tools:**
   - `rqt_image_view`, `rviz2`

8. **Terminal wrapper processes:**
   - Bash processes from gnome-terminal with colored headers
   - Bash processes containing launcher commands

9. **Orphaned terminal windows:**
   - `gnome-terminal --title` processes with no children

10. **Temporary files:**
    - `/tmp/.X*lock`
    - `/tmp/gz*` (Gazebo temp files)
    - `/tmp/AirSim*` (AirSim temp files)
    - `/tmp/test_input.jpg`, `/tmp/test_annotated.jpg`

**Kill strategy:**
- First tries `TERM` signal (graceful shutdown)
- Waits 1 second
- If still running, sends `KILL` signal (force kill)

**Verification:**
- Counts remaining processes after cleanup
- Shows colorized status for each category
- If any processes remain, provides manual cleanup commands

**Output:**
- Green: Process type successfully cleaned
- Red: Processes found and killed
- Yellow: Warning about remaining processes (if any)

**Exit status:**
- Shows total remaining processes
- Provides manual cleanup commands if needed

---

## Advanced Usage

### Chaining Scripts

```bash
# Clean, rebuild, and launch
./scripts/cleanup.sh && \
./scripts/rebuild.sh && \
./scripts/launch.sh --sim gazebo --debug
```

### Automation

```bash
# Add to crontab for scheduled builds
0 2 * * * cd ~/halcon1-system && ./scripts/rebuild.sh --clean >> ~/build.log 2>&1
```

### Environment Variables

Scripts respect these environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `ROS_DOMAIN_ID` | ROS2 domain ID | `0` |
| `GAZEBO_MODEL_PATH` | Gazebo model paths | (auto-configured) |
| `PX4_HOME_LAT` | PX4 home latitude | `47.397742` |
| `PX4_HOME_LON` | PX4 home longitude | `8.545594` |
| `GZ_VERSION` | Gazebo version | `harmonic` |

**Example:**
```bash
# Use different ROS domain
export ROS_DOMAIN_ID=42
./scripts/launch.sh --sim gazebo

# Set custom PX4 home location
export PX4_HOME_LAT=37.7749
export PX4_HOME_LON=-122.4194
./scripts/launch.sh --sim gazebo
```

## Common Workflows

### Development Workflow

```bash
# 1. Make code changes
vim src/ros2/modules/detection/detection/detection_node.py

# 2. Rebuild just that package
./scripts/rebuild.sh detection

# 3. Test in simulation
./scripts/launch.sh --sim gazebo --debug

# 4. Verify topic is publishing
ros2 topic hz /enemy/detection
```

### Testing Workflow

```bash
# 1. Clean environment
./scripts/cleanup.sh

# 2. Full clean rebuild
./scripts/rebuild.sh --clean --all

# 3. Validate everything
./scripts/validate.sh

# 4. Run tests
./scripts/launch.sh --sim gazebo --mode multi --debug
```

### Pre-Flight Checklist

```bash
# 1. Validate installation
./scripts/validate.sh

# 2. Test in Gazebo
./scripts/launch.sh --sim gazebo --mode multi --debug

# 3. Verify all topics publishing
ros2 topic hz /camera/image
ros2 topic hz /enemy/detection
ros2 topic hz /enemy/tracked
ros2 topic hz /fmu/in/trajectory_setpoint

# 4. Check for errors
ros2 node list
ros2 topic list
```

## Troubleshooting

### Script Won't Run

```bash
# Make executable
chmod +x ./scripts/launch.sh

# Check for syntax errors
bash -n ./scripts/launch.sh
```

### "Command not found"

```bash
# Source ROS2
source /opt/ros/humble/setup.bash

# Source workspace
source install/setup.bash
```

### Processes Won't Stop

```bash
# Use cleanup script
./scripts/cleanup.sh

# Manual kill if needed
pkill -9 -f "px4|gz|MicroXRCE|ros2"
```

### Build Failures

```bash
# Check logs
cat log/latest_build/<package_name>/stdout.log

# Clean and rebuild specific package
./scripts/rebuild.sh --clean detection
```

### Terminal emulator not found

```bash
# Install gnome-terminal
sudo apt install gnome-terminal

# Or use alternative
sudo apt install xterm
```

## See Also

- [Installation Guide](INSTALLATION.md) - Setup instructions
- [Development Guide](DEVELOPMENT.md) - Building and testing
- [Simulation Guide](SIMULATION.md) - Simulator usage
- [Architecture](ARCHITECTURE.md) - System design
