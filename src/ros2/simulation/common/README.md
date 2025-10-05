# Simulation Architecture

## Overview

Halcon1's simulation system is designed with **engine-agnostic** principles. The core Halcon1 logic (detection, tracking, guidance) works identically across all simulators without code changes.

## Supported Simulators

| Simulator | Status | Best For |
|-----------|--------|----------|
| **Gazebo Harmonic** | ✅ Fully Supported | Development, CI/CD, fast iteration |
| **AirSim** | ✅ Fully Supported | Computer vision, realistic rendering |
| **Isaac Sim** | 📋 Planned | GPU acceleration, ML training |

## Architecture Principles

### 1. Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                    Halcon1 Core Logic                       │
│            (Detection, Tracking, Guidance)                  │
│                                                             │
│  • Subscribes to: /camera/image, /fmu/out/*                │
│  • Publishes to: /fmu/in/trajectory_setpoint               │
│  • NEVER knows which simulator is running                  │
└─────────────────────────────────────────────────────────────┘
                            ↑
                            │ Standard ROS2 Topics
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Simulation Engine Layer                    │
│                   (Simulator-Specific)                      │
│                                                             │
│  • Gazebo: ros_gz_bridge                                   │
│  • AirSim: camera_bridge + viz_translator   │
│  • Isaac: omniverse_ros2_bridge                            │
│                                                             │
│  Converts simulator topics → Standard ROS2 topics          │
└─────────────────────────────────────────────────────────────┘
                            ↑
                            │ Simulator-Specific Interface
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Physics Engine                           │
│                                                             │
│  • Gazebo: ODE/Bullet physics                              │
│  • AirSim: PhysX + Unreal Engine                           │
│  • Isaac: PhysX 5 + RTX rendering                          │
└─────────────────────────────────────────────────────────────┘
```

### 2. Common Interfaces

All simulation engines implement `SimulationEngine` interface defined in `interfaces/sim_engine.py`:

```python
class SimulationEngine(ABC):
    @abstractmethod
    def validate_installation(self) -> Tuple[bool, str]:
        """Check if simulator is installed"""

    @abstractmethod
    def launch_simulator(self) -> bool:
        """Start the physics engine/3D environment"""

    @abstractmethod
    def launch_bridges(self) -> bool:
        """Start ROS2 bridges for this simulator"""

    @abstractmethod
    def get_camera_topic(self, drone_name: str) -> str:
        """Return camera topic name (e.g., /camera/image)"""

    @abstractmethod
    def get_px4_connection_config(self, instance_id: int) -> Dict:
        """MAVLink connection config for PX4"""

    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up all processes"""
```

### 3. Unified Launcher

Single entry point for all simulators:

```bash
# Launch Gazebo (fast, lightweight)
./scripts/launch.sh --sim gazebo

# Launch AirSim (photo-realistic)
./scripts/launch.sh --sim airsim

# Launch with debug visualizers (ally/enemy debug markers)
./scripts/launch.sh --sim gazebo --debug

# Multi-drone mode (launches enemy offboard control automatically)
./scripts/launch.sh --sim gazebo --mode multi

# Custom world
./scripts/launch.sh --sim gazebo --world custom_world
```

**Available Parameters:**
- `--sim <simulator>`: Simulator to use (gazebo, airsim) - default: gazebo
- `--mode <mode>`: Simulation mode (single, multi, hardware) - default: single
- `--debug`: Enable debug visualizers (ally_visualizer, enemy_visualizer for debug markers). Note: RViz2 always launches
- `--world <name>`: World/environment to load (simulator-specific) - default: default

The launcher (`simulation/common/launcher.py`):
1. Loads the requested simulation engine
2. Validates installation
3. Launches simulator, PX4, bridges, and Halcon1 pipeline
4. Handles cleanup on Ctrl+C

## Adding a New Simulator

Want to add Isaac Sim, Webots, or another simulator? Follow these steps:

### Step 1: Implement SimulationEngine Interface

Create `simulation/<simulator_name>/<simulator_name>_engine.py`:

```python
from sim_engine import SimulationEngine, SimulationEngineFactory

class MySimEngine(SimulationEngine):
    def get_name(self) -> str:
        return "My Simulator"

    def validate_installation(self) -> Tuple[bool, str]:
        # Check if installed
        return True, "Validated"

    def launch_simulator(self) -> bool:
        # Start simulator
        return True

    def launch_bridges(self) -> bool:
        # Start ROS2 bridges
        return True

    def get_px4_connection_config(self, instance_id: int) -> Dict:
        return {"protocol": "tcp", "port": 4560, "address": "localhost"}

    def get_camera_topic(self, drone_name: str) -> str:
        return "/camera/image"

    def get_px4_env_vars(self, drone_config: DroneConfig) -> Dict[str, str]:
        return {"PX4_SIM_MODEL": "none"}

    def cleanup(self) -> bool:
        # Clean up processes
        return True

# Register with factory
SimulationEngineFactory.register_engine("mysim", MySimEngine)
```

### Step 2: Create Configuration Directory

```bash
mkdir -p simulation/mysim/{config,launch,bridges}
```

Put simulator-specific configs, launch scripts, and bridge code here.

### Step 3: Register in Launcher

Edit `simulation/common/launcher.py` to import your engine:

```python
# Add this import
import mysim_engine
```

### Step 4: Test

```bash
# Test your new simulator
./scripts/launch.sh --sim mysim

# Test multi-drone mode
./scripts/launch.sh --sim mysim --mode multi

# Test with debug mode
./scripts/launch.sh --sim mysim --debug
```

### Step 5: Document

Create `simulation/mysim/README.md` explaining:
- Installation steps
- Configuration options
- Known limitations
- Example usage

## Directory Structure

```
simulation/
├── common/
│   ├── interfaces/
│   │   └── sim_engine.py          # Abstract base class
│   ├── launcher.py                 # Unified launcher (Python)
│   └── README.md                   # This file
├── gazebo/
│   ├── config/                     # Gazebo worlds, models
│   ├── launch/                     # Gazebo-specific scripts
│   ├── engine.py           # Gazebo implementation
│   └── README.md                   # Gazebo setup guide
├── airsim/
│   ├── config/
│   │   └── settings.json          # AirSim configuration
│   ├── launch/                     # AirSim-specific scripts
│   ├── bridges/                    # ROS2 bridge packages
│   ├── engine.py           # AirSim implementation
│   └── README.md                   # AirSim setup guide
└── isaac/
    ├── config/                     # USD scenes, configs
    ├── launch/                     # Isaac-specific scripts
    └── README.md                   # Isaac setup guide (planned)
```

## Benefits of This Architecture

✅ **Extensibility**: Add new simulators without touching core code
✅ **Maintainability**: Clear separation between simulation and logic
✅ **Testability**: Easy to test on fast simulator (Gazebo) before deploying to realistic one (AirSim)
✅ **Documentation**: Each simulator has its own docs and examples
✅ **Onboarding**: New developers understand structure immediately

## See Also

- [Gazebo Setup](../gazebo/README.md)
- [AirSim Setup](../airsim/README.md)
- [Isaac Sim Plans](../isaac/README.md)
- [Main Documentation](../../docs/README.md)
