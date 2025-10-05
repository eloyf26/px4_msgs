# Halcon1 Development Guide

## Building the Workspace

### Full Build

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### Build Specific Packages

```bash
# Build single package
colcon build --packages-select detection

# Build multiple packages
colcon build --packages-select detection tracking guidance

# Build with dependencies
colcon build --packages-up-to detection
```

### Clean Build

```bash
# Remove build artifacts
rm -rf build/ install/ log/

# Rebuild everything
colcon build --symlink-install
```

---

## Package Structure

Halcon1 uses two types of ROS2 packages:

### Python Packages (ament_python)

**Example:** `src/ros2/modules/detection/`

**Structure:**
```
detection/
├── package.xml          # Package metadata and dependencies
├── setup.py             # Python package configuration
├── resource/            # Package marker
└── detection/           # Python module
    ├── __init__.py
    ├── detection_node.py
    ├── detection_algorithm.py
    └── config.yaml
```

**setup.py:**
```python
from setuptools import setup

setup(
    name='detection',
    version='0.0.0',
    packages=['detection'],
    install_requires=[
        'setuptools',
        'ultralytics>=8.0.0',
        'opencv-python>=4.8.0',
    ],
    entry_points={
        'console_scripts': [
            'detection_node = detection.detection_node:main',
        ],
    },
)
```

**package.xml:**
```xml
<package format="3">
  <name>detection</name>
  <depend>rclpy</depend>
  <depend>msgs</depend>
  <depend>common_types</depend>
  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

### C++ Packages (ament_cmake)

**Example:** `src/ros2/modules/msgs/`

**Structure:**
```
msgs/
├── CMakeLists.txt       # Build configuration
├── package.xml          # Package metadata
└── msg/                 # Message definitions
    └── DroneDetection.msg
```

**CMakeLists.txt:**
```cmake
cmake_minimum_required(VERSION 3.8)
project(msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/DroneDetection.msg"
  DEPENDENCIES std_msgs
)

ament_package()
```

**package.xml:**
```xml
<package format="3">
  <name>msgs</name>
  <buildtool_depend>ament_cmake</buildtool_depend>
  <depend>rosidl_default_generators</depend>
  <depend>std_msgs</depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

---

## Creating a New Module

### Python Node Example

**1. Create package structure:**
```bash
cd src/ros2/modules
mkdir -p my_module/my_module
touch my_module/package.xml
touch my_module/setup.py
touch my_module/resource/my_module
touch my_module/my_module/__init__.py
touch my_module/my_module/my_node.py
```

**2. Write package.xml:**
```xml
<?xml version="1.0"?>
<package format="3">
  <name>my_module</name>
  <version>0.0.0</version>
  <description>My custom module</description>
  <maintainer email="dev@halcon.com">Halcon Team</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>
  <depend>msgs</depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

**3. Write setup.py:**
```python
from setuptools import setup

setup(
    name='my_module',
    version='0.0.0',
    packages=['my_module'],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/my_module']),
        ('share/my_module', ['package.xml']),
    ],
    install_requires=['setuptools'],
    entry_points={
        'console_scripts': [
            'my_node = my_module.my_node:main',
        ],
    },
)
```

**4. Write node (my_module/my_node.py):**
```python
import rclpy
from rclpy.node import Node
from msgs.msg import DroneDetection

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')

        # Subscriber
        self.sub = self.create_subscription(
            DroneDetection,
            '/enemy/detection',
            self.callback,
            10
        )

        # Publisher
        self.pub = self.create_publisher(
            DroneDetection,
            '/my_output',
            10
        )

        self.get_logger().info('MyNode initialized')

    def callback(self, msg):
        self.get_logger().info(f'Received: x={msg.x}, y={msg.y}')
        # Process and publish
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**5. Build and run:**
```bash
colcon build --packages-select my_module
source install/setup.bash
ros2 run my_module my_node
```

---

## Creating Custom Messages

**1. Add message file:**
```bash
cd src/ros2/modules/msgs/msg
nano MyMessage.msg
```

**MyMessage.msg:**
```
std_msgs/Header header
float64 x
float64 y
float64 z
float64[] velocities
```

**2. Update CMakeLists.txt:**
```cmake
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/DroneDetection.msg"
  "msg/MyMessage.msg"  # Add this line
  DEPENDENCIES std_msgs
)
```

**3. Rebuild:**
```bash
colcon build --packages-select msgs
source install/setup.bash
```

**4. Use in Python:**
```python
from msgs.msg import MyMessage

msg = MyMessage()
msg.header.stamp = self.get_clock().now().to_msg()
msg.x = 1.0
msg.y = 2.0
msg.z = 3.0
msg.velocities = [0.1, 0.2, 0.3]
```

---

## Testing

### Running Nodes Manually

```bash
# Source workspace
source install/setup.bash

# Run detection node
ros2 run detection detection_node

# Run with parameters
ros2 run detection detection_node --ros-args -p debug:=true

# Run with remapping
ros2 run detection detection_node --ros-args -r /camera/image:=/custom_camera
```

### Testing with Fake Data

```bash
# Publish fake detection
ros2 topic pub /enemy/detection msgs/DroneDetection '{
  header: {stamp: {sec: 0, nanosec: 0}, frame_id: "camera"},
  x: 320.0,
  y: 240.0,
  width: 50.0,
  height: 50.0
}'

# Echo output
ros2 topic echo /enemy/pose
```

### Checking Topic Rates

```bash
ros2 topic hz /camera/image        # Should be ~30 Hz
ros2 topic hz /enemy/detection     # Should be ~10 Hz
ros2 topic hz /enemy/pose          # Should be ~10 Hz
```

### Inspecting Messages

```bash
# Show message type
ros2 topic info /enemy/detection

# Show message structure
ros2 interface show msgs/DroneDetection

# Echo once
ros2 topic echo /enemy/detection --once
```

---

## Debugging

### Enable Debug Logging

```python
# In your node's __init__
self.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)
```

### ROS2 Launch with Debug

```bash
# Run with debug output
ros2 run detection detection_node --ros-args --log-level debug
```

### Visualize with RViz2

```bash
ros2 run rviz2 rviz2
```

### Monitor System

```bash
# List all nodes
ros2 node list

# List all topics
ros2 topic list

# Check node info
ros2 node info /detection_node

# View computational graph
rqt_graph
```

---

## Workflow Example

**Scenario:** Modify detection algorithm

```bash
# 1. Edit code
nano src/ros2/modules/detection/detection/detection_algorithm.py

# 2. Rebuild only detection package
colcon build --packages-select detection

# 3. Source workspace
source install/setup.bash

# 4. Test node
ros2 run detection detection_node

# 5. Check output in another terminal
ros2 topic echo /enemy/detection

# 6. If issues, check logs
ros2 run detection detection_node --ros-args --log-level debug
```

---

## See Also

- [Architecture](ARCHITECTURE.md) - System design
- [Scripts](SCRIPTS.md) - Launch script usage
- [Algorithms](ALGORITHMS.md) - Algorithm details
