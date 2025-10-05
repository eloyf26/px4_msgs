# Halcon1 Simulation & Hardware Integration

## Overview

Halcon1's **simulator-agnostic architecture** allows the same code to run on:
- Gazebo, AirSim, Isaac Sim (via plugin interface)
- Real hardware (physical drones)

Core nodes (detection, tracking, guidance) work identically across all platforms.

## Quick Start

```bash
# Gazebo (development)
./scripts/launch.sh --sim gazebo --mode multi --debug

# AirSim (photo-realistic)
./scripts/launch.sh --sim airsim

# Multi-drone scenario
./scripts/launch.sh --sim gazebo --mode multi
```

---

# Adding a New Simulator

## Interface Overview

All simulators implement `SimulationEngine` from `src/ros2/simulation/common/interfaces/sim_engine.py`.

**Required methods:**
- `validate_installation()` - Check if simulator installed
- `launch_simulator()` - Start physics engine
- `launch_bridges()` - Start ROS2 bridges
- `get_camera_topic()` - Return camera topic name
- `get_px4_connection_config()` - PX4 connection settings
- `cleanup()` - Terminate all processes

**Optional methods** (with defaults):
- `get_microxrce_port(instance_id)` - Default: `8888 + instance_id`
- `supports_feature(feature)` - Default: `False`

## Implementation Steps

### 1. Create Structure

```bash
mkdir -p src/ros2/simulation/mysim/{config,bridges}
```

### 2. Implement Engine

Create `src/ros2/simulation/mysim/engine.py`:

```python
from ..common.interfaces.sim_engine import SimulationEngine, SimulationEngineFactory

class MySimEngine(SimulationEngine):
    def get_name(self) -> str:
        return "My Simulator"

    def validate_installation(self) -> tuple:
        # Check if simulator installed
        if os.path.exists("/path/to/simulator"):
            return True, "Simulator found"
        return False, "Simulator not installed"

    def launch_simulator(self) -> bool:
        # Launch simulator process
        proc = subprocess.Popen(["mysim", "--headless"])
        self.processes.append(proc)
        return True

    def launch_bridges(self) -> bool:
        # Launch ROS2 bridges
        proc = subprocess.Popen(["ros2", "run", "mysim_bridge", "camera_node"])
        self.processes.append(proc)
        return True

    def get_camera_topic(self, drone_name: str = "Ally") -> str:
        return f"/{drone_name.lower()}/camera/image"

    def get_px4_connection_config(self, instance_id: int) -> dict:
        return {
            "protocol": "udp",
            "port": 14540 + instance_id,
            "address": "127.0.0.1"
        }

    def get_px4_env_vars(self, drone_config) -> dict:
        return {"PX4_SIM_MODEL": "iris"}

    def cleanup(self) -> bool:
        for proc in self.processes:
            proc.terminate()
        return True

# Register
SimulationEngineFactory.register_engine("mysim", MySimEngine)
```

### 3. Register in Launcher

Edit `src/ros2/simulation/common/launcher.py`:

```python
# Add import at top
import importlib.util

mysim_engine_path = Path(__file__).parent.parent / "mysim" / "engine.py"
spec = importlib.util.spec_from_file_location("mysim_engine_module", mysim_engine_path)
mysim_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mysim_engine)
```

### 4. Test

```bash
./scripts/launch.sh --sim mysim
```

---

# Real Hardware Integration

## Overview

Treat real drone as another "simulator" by implementing the same interface.

## Requirements

**Hardware:**
- Companion computer (Raspberry Pi 4 / Jetson Nano)
- Camera (USB or CSI)
- PX4 flight controller
- Serial connection (UART/Ethernet)

**Software:**
- ROS2 Humble on companion computer
- Camera driver (usb_cam / gscam)
- MicroXRCE-DDS Agent

## Implementation

### 1. Create Hardware Adapter

Create `src/ros2/simulation/hardware/hardware_adapter.py`:

```python
from ..common.interfaces.sim_engine import SimulationEngine, SimulationEngineFactory

class HardwareAdapter(SimulationEngine):
    def __init__(self, config):
        super().__init__(config)
        self.camera_device = "/dev/video0"
        self.px4_serial = "/dev/ttyTHS1"
        self.px4_baudrate = 921600

    def get_name(self) -> str:
        return "Real Hardware"

    def validate_installation(self) -> tuple:
        import os
        if not os.path.exists(self.camera_device):
            return False, f"Camera not found at {self.camera_device}"
        if not os.path.exists(self.px4_serial):
            return False, f"PX4 not connected at {self.px4_serial}"
        return True, "Hardware ready"

    def launch_simulator(self) -> bool:
        # No simulator - this is real hardware
        return True

    def launch_bridges(self) -> bool:
        # Launch camera driver
        cmd = [
            "ros2", "run", "usb_cam", "usb_cam_node_exe",
            "--ros-args",
            "-p", f"video_device:={self.camera_device}",
            "-p", "image_width:=640",
            "-p", "image_height:=480",
            "-p", "framerate:=30.0",
            "-r", "__ns:=/camera"
        ]
        proc = subprocess.Popen(cmd)
        self.processes.append(proc)
        return True

    def get_camera_topic(self, drone_name: str = "Ally") -> str:
        return "/camera/image_raw"

    def get_px4_connection_config(self, instance_id: int) -> dict:
        return {
            "protocol": "serial",
            "port": self.px4_serial,
            "baudrate": self.px4_baudrate
        }

    def get_px4_env_vars(self, drone_config) -> dict:
        return {}  # No PX4 SITL needed

    def cleanup(self) -> bool:
        for proc in self.processes:
            proc.terminate()
        return True

# Register
SimulationEngineFactory.register_engine("hardware", HardwareAdapter)
```

### 2. Configure PX4

Via QGroundControl or MAVLink shell:

```bash
# Enable MicroXRCE-DDS
param set UXRCE_DDS_CFG 1000  # Serial on TELEM2
param set SER_TEL2_BAUD 921600

# Offboard settings
param set COM_RCL_EXCEPT 4
param set COM_OBL_RC_ACT 0

param save
reboot
```

### 3. Install Camera Driver

```bash
# USB camera
sudo apt install ros-humble-usb-cam

# CSI camera (Jetson)
sudo apt install ros-humble-gscam
```

### 4. Launch

```bash
# SSH into companion computer
ssh ubuntu@drone-ip

# Launch Halcon1
./scripts/launch.sh --sim hardware
```

### 5. Safety Checklist

Before flight:
- [ ] Test in simulation first
- [ ] Verify camera: `ros2 topic hz /camera/image_raw`
- [ ] Verify PX4: `ros2 topic hz /fmu/out/vehicle_odometry`
- [ ] RC override enabled
- [ ] Emergency landing procedure ready
- [ ] Start with low-speed, high-altitude tests

---

# Simulator Comparison

| Feature | Gazebo | AirSim | Isaac Sim | Real Hardware |
|---------|--------|--------|-----------|---------------|
| **Setup** | 5 min | 15 min | 30 min | 2 hours |
| **Disk** | 500 MB | 5 GB | 10 GB | N/A |
| **Graphics** | Good | Photo-realistic | Ray-traced | Reality |
| **Performance** | Fast ⚡ | Moderate | Fast (GPU) | Real-time |
| **GPU Required** | No | No | Yes (NVIDIA) | Optional |
| **Best For** | Development | CV research | ML training | Validation |
| **Cost** | Free | Free | Free | $$$$ |

## When to Use

**Gazebo:**
- Rapid iteration
- CI/CD pipelines
- Algorithm testing

**AirSim:**
- Perception research
- Demo videos
- Training data collection

**Isaac Sim:**
- ML model training
- GPU-accelerated physics
- Synthetic data generation

**Real Hardware:**
- Final validation
- Actual flight conditions
- Real-world data

## Development Workflow

```
1. Prototype in Gazebo (fast iteration)
2. Validate in AirSim (realistic perception)
3. Optional: Train ML in Isaac Sim
4. Deploy to real hardware
```

---

# Advanced Topics

## Custom Camera Configuration

```python
drone_config = DroneConfig(
    name="Ally",
    instance_id=0,
    position=(0, 0, 2),
    camera_config={
        "width": 1280,
        "height": 720,
        "fov": 90.0,
        "frame_rate": 60
    }
)
```

## Network Configuration (Hardware)

On companion computer:

```bash
# Static IP
sudo nmcli con mod "WiFi" ipv4.addresses 192.168.1.100/24
sudo nmcli con mod "WiFi" ipv4.method manual

# Match ROS domain on ground station
export ROS_DOMAIN_ID=42
```

## Camera Calibration (Hardware)

```bash
# Install calibration tool
sudo apt install ros-humble-camera-calibration

# Run calibration
ros2 run camera_calibration cameracalibrator \
    --size 8x6 \
    --square 0.024 \
    image:=/camera/image_raw

# Save to ~/.ros/camera_info/camera.yaml
```

## See Also

- [Architecture](ARCHITECTURE.md) - System design
- [Installation](INSTALLATION.md) - Setup guide
- [Development](DEVELOPMENT.md) - Building and testing
- [Scripts](SCRIPTS.md) - Script documentation
