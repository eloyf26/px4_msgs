#!/bin/bash

# Halcon1 System Setup Script
# This script initializes all dependencies and builds the complete system
# Usage: ./setup.sh [--airsim]

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Parse command line arguments
INSTALL_GAZEBO=true
INSTALL_AIRSIM=false
VALIDATE_ONLY=false

for arg in "$@"; do
    case $arg in
        --gazebo)
            INSTALL_GAZEBO=true
            INSTALL_AIRSIM=false
            shift
            ;;
        --airsim)
            INSTALL_GAZEBO=false
            INSTALL_AIRSIM=true
            shift
            ;;
        --full)
            INSTALL_GAZEBO=true
            INSTALL_AIRSIM=true
            shift
            ;;
        --validate)
            VALIDATE_ONLY=true
            shift
            ;;
        --help)
            echo "Halcon1 Setup Script"
            echo ""
            echo "Usage: ./setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --gazebo     Build Gazebo dependencies only (default)"
            echo "  --airsim     Build AirSim dependencies + download environment (interactive)"
            echo "  --full       Build both Gazebo AND AirSim dependencies"
            echo "  --validate   Check what's installed and working"
            echo "  --help       Show this help message"
            echo ""
            echo "Note: AirSim installation includes an interactive menu to choose environment"
            echo "      (Blocks, Landscape, or City). You can skip and install manually later."
            exit 0
            ;;
        *)
            ;;
    esac
done

echo "=== Halcon1 System Setup ==="

# Function to verify Python dependencies
verify_python_dependencies() {
    local mode=$1  # "gazebo", "airsim", or "full"

    echo "→ Verifying Python dependencies..."

    local missing_packages=()
    local version_issues=()

    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        echo "✗ Python 3 not found"
        echo "  Install with: sudo apt install python3 python3-pip"
        exit 1
    fi

    # Core dependencies (always required)
    echo "  Checking core Python packages..."

    # Check ultralytics
    if ! python3 -c "import ultralytics" 2>/dev/null; then
        missing_packages+=("ultralytics")
    else
        local version=$(python3 -c "import ultralytics; print(ultralytics.__version__)" 2>/dev/null)
        echo "    ✓ ultralytics $version"
    fi

    # Check torch (ultralytics dependency)
    if ! python3 -c "import torch" 2>/dev/null; then
        missing_packages+=("torch")
    else
        local version=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null)
        echo "    ✓ torch $version"
    fi

    # Check opencv
    if ! python3 -c "import cv2" 2>/dev/null; then
        missing_packages+=("opencv-python")
    else
        local version=$(python3 -c "import cv2; print(cv2.__version__)" 2>/dev/null)
        echo "    ✓ opencv-python $version"
    fi

    # Check pyyaml
    if ! python3 -c "import yaml" 2>/dev/null; then
        missing_packages+=("PyYAML")
    else
        local version=$(python3 -c "import yaml; print(yaml.__version__)" 2>/dev/null)
        echo "    ✓ PyYAML $version"
    fi

    # Check numpy
    if ! python3 -c "import numpy" 2>/dev/null; then
        missing_packages+=("numpy")
    else
        local version=$(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null)
        echo "    ✓ numpy $version"
    fi

    # Check scipy
    if ! python3 -c "import scipy" 2>/dev/null; then
        missing_packages+=("scipy")
    else
        local version=$(python3 -c "import scipy; print(scipy.__version__)" 2>/dev/null)
        echo "    ✓ scipy $version"
    fi

    # AirSim-specific dependencies
    if [ "$mode" = "airsim" ] || [ "$mode" = "full" ]; then
        echo "  Checking AirSim Python packages..."

        # Check airsim
        if ! python3 -c "import airsim" 2>/dev/null; then
            missing_packages+=("airsim")
        else
            echo "    ✓ airsim installed"
        fi

        # Check msgpack-rpc-python
        if ! python3 -c "import msgpackrpc" 2>/dev/null; then
            missing_packages+=("msgpack-rpc-python")
        else
            echo "    ✓ msgpack-rpc-python installed"
        fi
    fi

    # Report results
    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo ""
        echo "✗ Missing Python packages detected:"
        for pkg in "${missing_packages[@]}"; do
            echo "  - $pkg"
        done
        echo ""
        echo "Install missing packages with:"
        if [ "$mode" = "airsim" ] || [ "$mode" = "full" ]; then
            echo "  pip3 install -r requirements.txt"
        else
            echo "  pip3 install ${missing_packages[@]}"
        fi
        echo ""
        read -p "Install missing packages now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "→ Installing Python packages..."
            if [ "$mode" = "airsim" ] || [ "$mode" = "full" ]; then
                pip3 install -r requirements.txt
                pip3 install msgpack-rpc-python
            else
                pip3 install ${missing_packages[@]}
            fi
            echo "✓ Python packages installed"
        else
            echo "✗ Cannot continue without required Python packages"
            exit 1
        fi
    else
        echo "  ✓ All required Python packages installed"
    fi
}

# Handle validation mode
if [ "$VALIDATE_ONLY" = true ]; then
    echo "→ Running validation checks..."
    exec "$SCRIPT_DIR/scripts/validate.sh"
    exit $?
fi

if [ "$INSTALL_GAZEBO" = true ] && [ "$INSTALL_AIRSIM" = true ]; then
    echo "→ Mode: FULL (Gazebo + AirSim)"
elif [ "$INSTALL_AIRSIM" = true ]; then
    echo "→ Mode: AirSim only"
elif [ "$INSTALL_GAZEBO" = true ]; then
    echo "→ Mode: Gazebo only (default)"
fi

# 1. Initialize and update git submodules
echo "→ Initializing git submodules..."
git submodule update --init --recursive

# 2. Install PX4 Toolchain (includes gazebo harmonic)
echo "→ Installing PX4 Toolchain with gazebo harmonic simulator..."
cd external/PX4-Autopilot
bash ./Tools/setup/ubuntu.sh
cd "$SCRIPT_DIR"

# 3. Build PX4 (optional, takes time)
read -p "Build PX4 SITL? This will take 10-20 minutes (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Building PX4 SITL..."
    cd external/PX4-Autopilot
    make px4_sitl_default
    cd "$SCRIPT_DIR"
fi

# 4. Build MicroXRCE-DDS-Agent
echo "→ Building MicroXRCE-DDS-Agent..."
cd external/Micro-XRCE-DDS-Agent
mkdir -p build
cd build
cmake ..
make -j$(nproc)
cd "$SCRIPT_DIR"

# 5. Install ROS2 Humble
echo "→ Installing ROS2 Humble..."
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install -y curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y ros-humble-desktop
echo "✓ ROS2 Humble installed"

# 6. Ensure ros_gz dependencies are installed
echo "→ Ensuring ros_gz dependencies are installed..."
sudo apt-get install -y \
    libgflags-dev \
    libgoogle-glog-dev \
    libtinyxml2-dev \
    libprotobuf-dev \
    ros-humble-actuator-msgs \
    ros-humble-gps-msgs \
    ros-humble-vision-msgs \
    ros-humble-tf2-ros \
    ros-humble-image-transport \
    ros-humble-nav-msgs \
    ros-humble-sensor-msgs \
    ros-humble-trajectory-msgs \
    ros-humble-rosgraph-msgs
echo "✓ ros_gz dependencies installed"

# 6b. Install AirSim ROS2 dependencies (optional)
if [ "$INSTALL_AIRSIM" = true ]; then
    echo "→ Installing AirSim ROS2 dependencies..."
    sudo apt-get install -y \
        ros-humble-tf2-sensor-msgs \
        ros-humble-tf2-geometry-msgs \
        ros-humble-mavros-msgs
    echo "✓ AirSim ROS2 dependencies installed"
fi

# 7. Initialize rosdep and setup rules for Gazebo Harmonic
echo "→ Setting up rosdep rules for Gazebo Harmonic..."
sudo mkdir -p /etc/ros/rosdep/sources.list.d
sudo bash -c 'wget https://raw.githubusercontent.com/osrf/osrf-rosdep/master/gz/00-gazebo.list -O /etc/ros/rosdep/sources.list.d/00-gazebo.list'
sudo apt update
sudo apt install python3-rosdep -y
sudo rosdep init || true  # Don't fail if already initialized
rosdep update
rosdep resolve gz-harmonic
echo "✓ Rosdep rules for Gazebo Harmonic installed"

# 8. Clone ros_gz from source (humble branch) to simulation/gazebo/bridges/
if [ "$INSTALL_GAZEBO" = true ]; then
    echo "→ Ensuring ros_gz source (humble branch)..."
    if [ -d "simulation/gazebo/bridges/.git" ]; then
        echo "↷ ros_gz already present; skipping clone"
    else
        echo "→ Cloning ros_gz from source (humble branch)..."
        mkdir -p simulation/gazebo
        cd simulation/gazebo
        git clone https://github.com/gazebosim/ros_gz.git -b humble bridges
        cd "$SCRIPT_DIR"
        echo "✓ ros_gz cloned from humble branch"
    fi
    export GZ_VERSION=harmonic # Required for building ros_gz in step 10
    echo "✓ GZ_VERSION=harmonic exported"
fi

# Install rqt_image_view and cv_bridge for visualizing camera images
sudo apt update
sudo apt install -y ros-humble-rqt-image-view ros-humble-cv-bridge

# Install Python dependencies from centralized requirements.txt
echo "→ Installing Python dependencies..."
pip3 install --upgrade pip

if [ "$INSTALL_AIRSIM" = true ]; then
    echo "  Installing all dependencies (including AirSim)..."
    pip3 install -r requirements.txt
    pip3 install msgpack-rpc-python  # Additional AirSim dependency
    echo "✓ All Python dependencies installed (including AirSim)"
else
    echo "  Installing core dependencies (excluding AirSim)..."
    # Install everything except airsim
    pip3 install ultralytics torch torchvision opencv-python opencv-contrib-python
    pip3 install numpy scipy PyYAML
    pip3 install pytest pytest-cov flake8
    pip3 install colcon-common-extensions empy
    echo "✓ Core Python dependencies installed"
    echo "↷ Skipping AirSim dependencies (use --airsim to enable)"
fi

# 9. Build ROS2 workspace
echo "→ Installing ROS2 build tools..."
sudo apt install -y \
    python3-colcon-common-extensions \
    ros-humble-rosidl-default-generators \
    ros-humble-ament-cmake \
    ros-humble-ament-cmake-cppcheck \
    ros-humble-ament-cmake-cpplint \
    ros-humble-ament-cmake-flake8 \
    ros-humble-ament-cmake-pep257 \
    ros-humble-ament-cmake-uncrustify \
    ros-humble-ament-lint-auto \
    ros-humble-ament-lint-common
echo "✓ ROS2 build tools installed"

echo "→ Building ROS2 packages..."
cd ws_ros2
source /opt/ros/humble/setup.bash

# Verify Python dependencies before building
if [ "$INSTALL_GAZEBO" = true ] && [ "$INSTALL_AIRSIM" = true ]; then
    verify_python_dependencies "full"
elif [ "$INSTALL_AIRSIM" = true ]; then
    verify_python_dependencies "airsim"
else
    verify_python_dependencies "gazebo"
fi

# Clean up old directories from pre-reorganization
echo "→ Cleaning up old package directories..."
if [ -d "src/airsim" ]; then
    echo "  ↷ Removing old airsim directory..."
    rm -rf src/airsim
fi
# Remove duplicate PX4 packages (they should only be in px4_bridges/)
for pkg in px4_msgs px4-offboard px4_ros_com; do
    if [ -d "src/$pkg" ]; then
        echo "  ↷ Removing duplicate $pkg directory (using px4_bridges/ instead)..."
        rm -rf "src/$pkg"
    fi
done

# Clean up old builds from renamed packages (halcon1_* → *)
echo "→ Cleaning up old package builds from rename..."
if [ -d "build/halcon1_detection" ] || [ -d "install/halcon1_detection" ]; then
    echo "  ↷ Removing old halcon1_* build and install directories..."
    rm -rf build/halcon1_* install/halcon1_*
    echo "  ✓ Old package builds removed"
fi

echo "  ✓ Cleanup complete"

# Create organized symlinks structure
echo "→ Creating organized symlinks for external packages..."
mkdir -p src/symlinks/gazebo src/symlinks/airsim

# Clean up old symlinks if they exist
for old_symlink in ros_gz adversarial camera_bridge viz_translator; do
    if [ -L "src/$old_symlink" ]; then
        echo "  ↷ Removing old symlink: src/$old_symlink"
        rm "src/$old_symlink"
    fi
done

# Common simulation packages
if [ ! -L "src/symlinks/enemy_control" ]; then
    ln -sf ../../../simulation/common/debug/enemy_control src/symlinks/enemy_control
    echo "  ✓ Created symlink for enemy_control"
fi

# Gazebo-specific packages
if [ ! -L "src/symlinks/gazebo/enemy_visualizer" ]; then
    ln -sf ../../../../simulation/gazebo/debug/enemy_visualizer src/symlinks/gazebo/enemy_visualizer
    echo "  ✓ Created symlink for enemy_visualizer (Gazebo)"
fi

if [ ! -L "src/symlinks/gazebo/ros_gz" ]; then
    ln -sf ../../../../simulation/gazebo/bridges src/symlinks/gazebo/ros_gz
    echo "  ✓ Created symlink for ros_gz"
fi

# AirSim-specific packages (created later if --airsim enabled)

echo "  ✓ Symlinks structure created"

# 10. Build in correct order

# Build Gazebo packages if requested
if [ "$INSTALL_GAZEBO" = true ]; then
    echo "→ Building Gazebo packages..."

    colcon build --packages-select ros_gz_interfaces
    colcon build --packages-select ros_gz_sim
    colcon build --packages-select ros_gz_bridge
    colcon build --packages-select ros_gz_image
    colcon build --packages-select ros_gz_sim_demos
    colcon build --packages-select ros_gz

    # Build Gazebo visualizer
    echo "→ Building Gazebo enemy visualizer..."
    colcon build --packages-select enemy_visualizer
    echo "  ✓ Gazebo packages built"
else
    echo "↷ Skipping Gazebo packages (use --gazebo or --full to enable)"
fi

# Build enemy control (common across simulators)
echo "→ Building enemy control..."
colcon build --packages-select enemy_control
echo "  ✓ Enemy control built"

# Build PX4 messages first (required by detection/tracking/guidance)
echo "→ Building PX4 message definitions..."
colcon build --packages-select px4_msgs

# Build core packages
echo "→ Building core Halcon1 packages..."
colcon build --packages-select msgs
colcon build --packages-select common_types transforms algorithms
colcon build --packages-select detection tracking guidance
colcon build --packages-select ally_visualizer
colcon build --packages-select bringup

# Skip PX4 bridge packages (no longer needed)
# px4_ros_com and px4_offboard were removed as unused

# Build AirSim packages (optional)
if [ "$INSTALL_AIRSIM" = true ]; then
    echo "→ Building AirSim packages..."

    # Create AirSim symlinks
    if [ ! -L "src/symlinks/airsim/camera_bridge" ]; then
        ln -sf ../../../simulation/airsim/debug/camera_bridge src/symlinks/airsim/camera_bridge
        echo "  ✓ Created symlink for camera_bridge"
    fi

    if [ ! -L "src/symlinks/airsim/viz_translator" ]; then
        ln -sf ../../../simulation/airsim/debug/viz_translator src/symlinks/airsim/viz_translator
        echo "  ✓ Created symlink for viz_translator"
    fi

    colcon build --packages-select camera_bridge
    colcon build --packages-select viz_translator
    echo "  ✓ AirSim packages built"

    # Copy AirSim settings.json to user directory
    echo "→ Setting up AirSim configuration..."
    AIRSIM_CONFIG_DIR="$HOME/Documents/AirSim"
    AIRSIM_SETTINGS="$SCRIPT_DIR/simulation/airsim/config/settings.json"

    mkdir -p "$AIRSIM_CONFIG_DIR"

    if [ -f "$AIRSIM_CONFIG_DIR/settings.json" ]; then
        echo "  ⚠ Existing settings.json found, creating backup..."
        cp "$AIRSIM_CONFIG_DIR/settings.json" "$AIRSIM_CONFIG_DIR/settings.json.backup_$(date +%Y%m%d_%H%M%S)"
    fi

    cp "$AIRSIM_SETTINGS" "$AIRSIM_CONFIG_DIR/settings.json"
    echo "  ✓ AirSim settings.json copied to $AIRSIM_CONFIG_DIR"

    # Validate JSON syntax
    if command -v python3 &> /dev/null; then
        if python3 -c "import json; json.load(open('$AIRSIM_CONFIG_DIR/settings.json'))" 2>/dev/null; then
            echo "  ✓ Settings.json validated successfully"
        else
            echo "  ⚠ Warning: settings.json may have syntax errors"
        fi
    fi

    # AirSim Environment Installation Menu
    echo ""
    echo "=== AirSim Environment Setup ==="
    echo "AirSim requires a pre-built Unreal Engine environment to run."
    echo ""
    echo "Choose an environment to download:"
    echo "  1) Blocks          (~400MB, fast, simple testing)"
    echo "  2) Landscape       (~5GB, realistic outdoor)"
    echo "  3) City            (~8GB, urban environment)"
    echo "  4) Skip            (install manually later)"
    echo ""
    read -p "Enter choice [1-4] (default: 1): " env_choice

    case "${env_choice:-1}" in
        1)
            ENV_NAME="Blocks"
            ENV_URL="https://github.com/microsoft/AirSim/releases/download/v1.8.1/Blocks.zip"
            ENV_SIZE="~400MB"
            ENV_DIR="LinuxBlocks1.8.1"
            ENV_EXEC="Blocks.sh"
            ;;
        2)
            ENV_NAME="Landscape"
            ENV_URL="https://github.com/microsoft/AirSim/releases/download/v1.8.1/LandscapeMountains.zip"
            ENV_SIZE="~5GB"
            ENV_DIR="LandscapeMountains"
            ENV_EXEC="LandscapeMountains.sh"
            ;;
        3)
            ENV_NAME="City"
            ENV_URL="https://github.com/microsoft/AirSim/releases/download/v1.8.1/CityEnviron.zip"
            ENV_SIZE="~8GB"
            ENV_DIR="CityEnviron"
            ENV_EXEC="CityEnviron.sh"
            ;;
        4)
            echo "↷ Skipping AirSim environment installation"
            ENV_NAME=""
            ;;
        *)
            echo "⚠ Invalid choice, defaulting to Blocks"
            ENV_NAME="Blocks"
            ENV_URL="https://github.com/microsoft/AirSim/releases/download/v1.8.1/Blocks.zip"
            ENV_SIZE="~400MB"
            ENV_DIR="LinuxBlocks1.8.1"
            ENV_EXEC="Blocks.sh"
            ;;
    esac

    # Download and install if not skipped
    if [ -n "$ENV_NAME" ]; then
        AIRSIM_ENV_DIR="$HOME/AirSimEnvironments"
        echo ""
        echo "→ Installing AirSim ${ENV_NAME} environment (${ENV_SIZE})..."

        mkdir -p "$AIRSIM_ENV_DIR"
        cd "$AIRSIM_ENV_DIR"

        if [ -d "$ENV_DIR" ]; then
            echo "  ✓ ${ENV_NAME} already installed at $AIRSIM_ENV_DIR/$ENV_DIR"
        else
            echo "  → Downloading ${ENV_NAME}... (this may take a while)"
            wget --progress=bar:force "$ENV_URL" -O "${ENV_NAME}.zip"

            echo "  → Extracting..."
            unzip -q "${ENV_NAME}.zip"
            rm "${ENV_NAME}.zip"

            chmod +x "${ENV_DIR}/LinuxNoEditor/${ENV_EXEC}"
            echo "  ✓ ${ENV_NAME} installed successfully"
        fi

        cd "$SCRIPT_DIR"
        AIRSIM_ENV_INSTALLED="$AIRSIM_ENV_DIR/$ENV_DIR/LinuxNoEditor/$ENV_EXEC"
    fi
else
    echo "↷ Skipping AirSim packages (use --airsim or --full to enable)"
fi

cd "$SCRIPT_DIR"

# 11. Make all scripts executable
echo "→ Making scripts executable..."
chmod +x scripts/*.sh
echo "✓ All scripts are now executable"

echo "=== Setup Complete ==="
echo ""

echo "🚀 Launch the system:"
echo ""
echo "  Unified Launcher (recommended):"
echo "    ./scripts/launch.sh --sim gazebo         # Launch with Gazebo"
echo "    ./scripts/launch.sh --sim airsim         # Launch with AirSim"
echo "    ./scripts/launch.sh --sim gazebo --debug # With RViz2 visualization"
echo "    ./scripts/launch.sh --sim gazebo --mode multi  # Multi-drone simulation"
echo ""
echo "  Validation:"
echo "    ./scripts/launch.sh --sim gazebo --validate    # Check Gazebo installation"
echo "    ./scripts/launch.sh --sim airsim --validate    # Check AirSim installation"
echo "    ./scripts/launch.sh --list-sims                # List available simulators"
echo ""

if [ "$INSTALL_AIRSIM" = true ]; then
    echo "  AirSim Setup:"
    if [ -n "$AIRSIM_ENV_INSTALLED" ]; then
        echo "    1. Launch AirSim: cd $(dirname "$AIRSIM_ENV_INSTALLED") && ./$(basename "$AIRSIM_ENV_INSTALLED")"
        echo "    2. In another terminal: ./scripts/launch.sh --sim airsim"
    else
        echo "    1. Download environment: ./scripts/install_airsim_env.sh --blocks"
        echo "    2. Launch AirSim: cd ~/AirSimEnvironments/<env>/ && ./<env>.sh"
        echo "    3. In another terminal: ./scripts/launch.sh --sim airsim"
    fi
    echo ""
    echo "  ✓ AirSim configured at ~/Documents/AirSim/settings.json"
    echo "  📖 See: simulation/airsim/README.md"
    echo ""
fi

if [ "$INSTALL_GAZEBO" = true ]; then
    echo "  Gazebo Setup:"
    echo "    Just run: ./scripts/launch.sh --sim gazebo"
    echo ""
    echo "  📖 See: simulation/gazebo/README.md"
    echo ""
fi

echo "🔧 Development Tools:"
echo "  cd ws_ros2 && colcon build --packages-select <package_name>"
echo "  cd ws_ros2 && colcon build                      # Rebuild all packages"
echo ""
echo "📊 Available ROS2 Topics:"
echo "  /camera/image       - Camera images (sensor_msgs/Image)"
echo "  /camera/camera_info - Camera calibration info"
echo "  /enemy/detection    - Target detections"
echo "  /enemy/tracked      - Target tracking"
echo "  /interception/command - Interception commands"
echo ""
echo "Source ROS2 workspace in new terminals:"
echo "  source $SCRIPT_DIR/ws_ros2/install/setup.bash"
echo ""
