# Python Dependencies for Halcon1 System

This document explains the Python dependencies used in the Halcon1 drone interception system.

## Requirements File

All Python dependencies are centralized in `requirements.txt` at the repository root.

## Installation

### Full Installation (including AirSim)
```bash
pip3 install -r requirements.txt
pip3 install msgpack-rpc-python  # Additional AirSim dependency
```

### Core Only (excluding AirSim)
```bash
pip3 install ultralytics torch torchvision opencv-python opencv-contrib-python
pip3 install numpy scipy PyYAML
pip3 install pytest pytest-cov flake8
```

### Automated Installation
The `setup.sh` script handles dependency installation automatically:
```bash
./setup.sh --gazebo  # Core dependencies only
./setup.sh --airsim  # Core + AirSim dependencies
./setup.sh --full    # Everything
```

## Dependency Categories

### Deep Learning & Computer Vision
- **ultralytics** (8.3.204) - YOLO object detection models
- **torch** (2.8.0) - PyTorch deep learning framework
- **torchvision** (0.23.0) - Vision models and transforms
- **opencv-python** (4.9.0.80) - Computer vision library
- **opencv-contrib-python** (4.9.0.80) - Additional OpenCV modules

### Scientific Computing
- **numpy** (1.26.4) - Numerical computing
- **scipy** (1.15.3) - Scientific computing (used in utils/coordinate_transform)

### Configuration & Data
- **PyYAML** (6.0.3) - YAML configuration file parsing

### Simulation (Optional)
- **airsim** (1.8.1) - Microsoft AirSim Python client
- **msgpack-rpc-python** - AirSim RPC communication

### Development & Testing
- **pytest** (6.2.5) - Unit testing framework
- **pytest-cov** (3.0.0) - Code coverage reporting
- **flake8** (4.0.1) - Code linting

### Build Tools
- **colcon-common-extensions** (0.3.0) - ROS2 build tools
- **empy** (3.3.4) - Template processing for message generation

### Additional Utilities
- **pandas** (2.3.3) - Data analysis (for data logging)
- **matplotlib** (3.10.6) - Plotting and visualization

## ROS2 Dependencies

The following are typically installed via `apt` (not pip):
- **rclpy** - ROS2 Python client library
- **cv_bridge** - ROS2-OpenCV bridge
- **px4_msgs** - PX4 message definitions
- **geometry_msgs**, **sensor_msgs**, **nav_msgs**, **std_msgs** - ROS2 standard messages

These are installed automatically by the setup script via:
```bash
sudo apt install ros-humble-cv-bridge ros-humble-rqt-image-view
```

## Module-Specific Dependencies

### Detection Module (`detection`)
- ultralytics (YOLO models)
- opencv-python (image processing)
- numpy (array operations)
- PyYAML (config loading)

### Tracking Module (`tracking`)
- numpy (coordinate transformations)
- scipy (optimization, if used)

### Guidance Module (`guidance`)
- numpy (navigation math)
- scipy (optimization, if used)

### Utils Module (`utils`)
- scipy (coordinate transformations)
- numpy (math operations)

### AirSim Bridges (`camera_bridge`, `viz_translator`)
- airsim (simulator interface)
- opencv-python (image conversion)
- msgpack-rpc-python (RPC communication)

## Validation

Check if all dependencies are installed:
```bash
./setup.sh --validate
# or
./scripts/validate.sh
```

## Upgrading Dependencies

To update all dependencies to their latest compatible versions:
```bash
pip3 install --upgrade -r requirements.txt
```

**Warning**: Test thoroughly after upgrading, especially:
- PyTorch/ultralytics compatibility
- OpenCV API changes
- NumPy/SciPy breaking changes

## Dependency Pinning

All versions are pinned to ensure reproducibility. The pinned versions are:
- Tested and working together
- Compatible with ROS2 Humble
- Compatible with CUDA 12.x (for GPU acceleration)

## Troubleshooting

### Import Errors
If you get import errors after installation:
```bash
# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Verify package installation
pip3 list | grep <package-name>
```

### CUDA/PyTorch Issues
For GPU acceleration, ensure CUDA toolkit matches PyTorch:
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```

### ROS2 Package Conflicts
If ROS2 packages conflict with pip packages:
```bash
# Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Virtual Environment (Optional)

For isolated development:
```bash
# Create virtual environment
python3 -m venv halcon_env
source halcon_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Remember to source ROS2 after activating venv
source /opt/ros/humble/setup.bash
source ws_ros2/install/setup.bash
```

## CI/CD Integration

For automated testing/deployment:
```bash
# Install in CI pipeline
pip3 install --no-cache-dir -r requirements.txt

# Run tests
pytest ws_ros2/src/Halcon1/modules/
```
