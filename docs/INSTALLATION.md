# Halcon1 Installation Guide

## Prerequisites

### Operating System
- **Required:** Ubuntu 22.04 LTS


### Required Software

#### 1. Python 3.10+

Ubuntu 22.04 comes with Python 3.10 by default. Verify:

```bash
python3 --version  # Should show 3.10.x 
```

#### 2. Git

```bash
sudo apt install -y git git-lfs
```

## Installation Methods

### Method 1: Automated Setup (Recommended)

#### For both simulation engines (Gazebo + Airsim)
```bash
# Clone repository with submodules
git clone --recursive https://github.com/eloyf26/halcon1-system.git
cd halcon1-system

# Run setup script
./setup.sh --full
```

#### For Gazebo Simulation (Fast, Lightweight)

```bash
# Clone repository with submodules
git clone --recursive https://github.com/eloyf26/halcon1-system.git
cd halcon1-system

# Run setup script
./setup.sh --gazebo
```

#### For AirSim Simulation (Photo-Realistic)

```bash
# Clone repository
git clone --recursive https://github.com/eloyf26/halcon1-system.git
cd halcon1-system

# Run setup for AirSim
./setup.sh --airsim

```

## Python Dependencies Explained

### Core Dependencies (Required)

#### Deep Learning & Computer Vision
- **ultralytics** (8.3.204) - YOLOv8 detection models
- **torch** (2.8.0) - PyTorch deep learning framework
- **torchvision** (0.23.0) - Vision models and transforms
- **opencv-python** (4.9.0.80) - Computer vision library
- **opencv-contrib-python** (4.9.0.80) - Additional OpenCV modules

#### Scientific Computing
- **numpy** (1.26.4) - Numerical computing
- **scipy** (1.15.3) - Scientific computing (coordinate transforms)

#### Configuration
- **PyYAML** (6.0.3) - YAML configuration file parsing

### Optional Dependencies

#### Simulation
- **airsim** (1.8.1) - AirSim Python client (only for AirSim)
- **msgpack-rpc-python** - AirSim RPC communication (only for AirSim)

#### Development & Testing
- **pytest** (6.2.5) - Unit testing
- **pytest-cov** (3.0.0) - Code coverage
- **flake8** (4.0.1) - Code linting

#### Data Analysis (Optional)
- **pandas** (2.3.3) - Data logging/analysis
- **matplotlib** (3.10.6) - Plotting/visualization

### GPU Acceleration (Optional)

For real-time detection, install CUDA-enabled PyTorch:

```bash
# Check CUDA version
nvidia-smi

# Install CUDA-enabled PyTorch (for CUDA 12.x)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Verify GPU availability
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Verification

### Check Installation

```bash
# Validate setup
./scripts/validate.sh
```

Expected output:
```
✓ ROS2 Humble installed
✓ Python 3.10+ installed
✓ PX4-Autopilot built
✓ Micro-XRCE-DDS-Agent built
✓ ROS2 packages built
✓ Python dependencies installed
✓ Gazebo Harmonic installed (if --gazebo)
✓ AirSim installed (if --airsim)
```

### Quick Test

#### Test Gazebo

```bash
# Launch Gazebo simulation
./scripts/launch.sh --sim gazebo

# In another terminal, check topics
source ws_ros2/install/setup.bash
ros2 topic list | grep camera
# Should show: /camera/image, /camera/camera_info
```

Press Ctrl+C to stop.

#### Test AirSim

```bash
# Launch Halcon1
cd ~/halcon1-system
./scripts/launch.sh --sim airsim
```

Check that camera topics are publishing:
```bash
ros2 topic hz /camera/image
# Should show ~30 Hz
```

### Getting Help

1. Run validation script: `./scripts/validate.sh`
2. Consult [PX4 Documentation](https://docs.px4.io/)
3. Consult [AirSim Documentation](https://microsoft.github.io/AirSim/)

## Uninstall

```bash
# Remove repository
rm -rf halcon1-system

# Remove Python packages (optional)
pip3 uninstall ultralytics torch torchvision opencv-python opencv-contrib-python numpy scipy PyYAML airsim

# Remove ROS2 (optional)
sudo apt remove ros-humble-*
sudo apt autoremove
```

## Next Steps

After installation:
1. Read [Simulation Guide](SIMULATION.md) to launch your first simulation
2. Review [Architecture](ARCHITECTURE.md) to understand the system
3. Check [Development Guide](DEVELOPMENT.md) to start contributing
4. Explore [Algorithms](ALGORITHMS.md) to learn about detection/tracking/guidance

## See Also

- [Scripts Documentation](SCRIPTS.md) - Detailed script usage
- [Main README](../README.md) - Quick start guide
