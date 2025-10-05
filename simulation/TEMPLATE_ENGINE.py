#!/usr/bin/env python3
"""
TEMPLATE: New Simulation Engine Implementation

This template shows you exactly what to implement for a new simulator.

INSTRUCTIONS:
1. Copy this file to simulation/<your_sim>/engine.py
2. Search for "TODO" and fill in your simulator's specific details
3. Delete all comments marked with "# DELETE THIS COMMENT"
4. Test with: ./scripts/launch.sh --sim <your_sim>

Only implement the methods marked REQUIRED.
Methods marked OPTIONAL can be left as-is (they have sensible defaults in the base class).
"""

import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "common" / "base"))
from engine_base import SimulationEngineBase  # DELETE THIS COMMENT: Import base class

sys.path.insert(0, str(Path(__file__).parent.parent / "common" / "interfaces"))
from sim_engine import DroneConfig, SimulationEngineFactory  # DELETE THIS COMMENT: Import factory


class MySimEngine(SimulationEngineBase):  # TODO: Rename class (e.g., IsaacSimEngine)
    """
    TODO: One-line description of your simulator

    Example: "Isaac Sim simulation engine with GPU-accelerated physics"
    """

    # DELETE THIS COMMENT: Optional configuration constants
    DEFAULT_WORLD = "default"  # TODO: Change if your sim has a different default
    AVAILABLE_WORLDS = ["default", "world1", "world2"]  # TODO: List your worlds

    def __init__(self, config):
        """
        Initialize your simulation engine.

        You get these for free from SimulationEngineBase:
        - self.repo_root: Path to halcon1-system/
        - self.px4_dir: Path to PX4-Autopilot/
        - self.ws_ros2: Path to ws_ros2/
        - self.processes: List to track spawned processes
        - self._launch_in_terminal(): Method to launch processes in terminals
        - self._detect_terminal(): Method to detect available terminals
        """
        super().__init__(config)

        # TODO: Add any simulator-specific paths here
        # Example:
        # self.config_dir = self.repo_root / "simulation" / "mysim" / "config"
        # self.sim_executable = Path("/opt/mysim/bin/mysim")

    # ========================================================================
    # REQUIRED METHODS (you must implement these)
    # ========================================================================

    def get_name(self) -> str:
        """
        Return the name of your simulator (shown in logs).

        Example: return "Isaac Sim"
        """
        return "My Simulator"  # TODO: Change to your simulator name

    def validate_installation(self) -> Tuple[bool, str]:
        """
        Check if your simulator is properly installed.

        Return (True, "success message") if installed
        Return (False, "error message with fix instructions") if not

        Example checks:
        - Simulator executable exists
        - Required Python packages installed
        - License valid
        - ROS2 bridge packages built
        """
        # TODO: Implement your installation checks

        # Example: Check if simulator command exists
        import shutil
        if not shutil.which("mysim"):
            return False, "Simulator not found. Install with: sudo apt install mysim"

        # Example: Check for required Python package
        try:
            import mysim_python_api
        except ImportError:
            return False, "Python API not installed. Run: pip install mysim-api"

        # Example: Check PX4 is built
        px4_binary = self.px4_dir / "build" / "px4_sitl_default" / "bin" / "px4"
        if not px4_binary.exists():
            return False, f"PX4 not built. Run: cd {self.px4_dir} && make px4_sitl_default"

        return True, "Installation validated successfully"

    def launch_simulator(self) -> bool:
        """
        Start your physics engine/3D environment.

        Use self._launch_in_terminal() to launch GUI processes.
        Track processes by appending to self.processes.

        Return True if successful, False otherwise.
        """
        print(f"[{self.get_name()}] Launching simulator...")

        # TODO: Implement simulator launch

        # Example: Launch in terminal
        # sim_cmd = ["/opt/mysim/bin/mysim", "--world", self.config.world]
        # proc = self._launch_in_terminal(
        #     title="My Simulator",
        #     cmd=sim_cmd,
        #     color="blue"
        # )
        #
        # if proc:
        #     self.processes.append(("simulator", proc))
        #     print(f"[{self.get_name()}] ✓ Simulator started")
        #     time.sleep(5)  # Wait for simulator to initialize
        #     return True
        # else:
        #     print(f"[{self.get_name()}] ERROR: Failed to start simulator")
        #     return False

        return True  # DELETE THIS LINE after implementing

    def launch_bridges(self) -> bool:
        """
        Launch ROS2 bridges to convert simulator topics to standard topics.

        Required bridges:
        - Camera: simulator camera → /camera/image, /camera/camera_info
        - Any other simulator-specific topics

        Use self._launch_in_terminal() to launch bridge processes.

        Return True if successful, False otherwise.
        """
        print(f"[{self.get_name()}] Launching ROS2 bridges...")

        # TODO: Implement bridge launches

        ws_setup = self.ws_ros2 / "install" / "setup.bash"

        # Example: Launch camera bridge
        # camera_cmd = [
        #     "bash", "-c",
        #     f"source /opt/ros/humble/setup.bash && "
        #     f"source {ws_setup} && "
        #     f"ros2 run my_camera_bridge camera_bridge"
        # ]
        #
        # proc = self._launch_in_terminal(
        #     title="Camera Bridge",
        #     cmd=camera_cmd,
        #     color="green"
        # )
        #
        # if proc:
        #     self.processes.append(("camera_bridge", proc))
        #     print(f"[{self.get_name()}] ✓ Camera bridge started")
        #     time.sleep(2)
        # else:
        #     return False

        return True  # DELETE THIS LINE after implementing

    def get_camera_topic(self, drone_name: str = "Ally") -> str:
        """
        Return the ROS2 topic name where camera images are published.

        This should be the FINAL topic after your bridge remapping.
        Halcon1 expects /camera/image (standard).
        """
        return "/camera/image"  # TODO: Verify this matches your bridge output

    def get_px4_connection_config(self, instance_id: int) -> Dict:
        """
        Return PX4 MAVLink connection configuration.

        Return dict with keys:
        - protocol: "tcp" or "udp"
        - port: Port number
        - address: Usually "localhost"

        Most simulators use:
        - TCP port 4560 (lockstep mode like AirSim)
        - UDP port 14560+instance_id (like Gazebo)
        """
        # TODO: Choose protocol and port
        return {
            "protocol": "tcp",  # or "udp"
            "port": 4560,       # or 14560 + instance_id for UDP
            "address": "localhost"
        }

    def get_px4_env_vars(self, drone_config: DroneConfig) -> Dict[str, str]:
        """
        Return environment variables needed for PX4 SITL.

        Required vars:
        - PX4_SIM_MODEL: Model name (or "none" if simulator provides physics)
        - PX4_SYS_AUTOSTART: Usually "4001" for quadcopter

        Optional vars (simulator-specific):
        - PX4_SIM_HOST: For TCP connections
        - PX4_GZ_MODEL_POSE: For Gazebo spawn position
        - etc.
        """
        # TODO: Implement environment variables
        return {
            "PX4_SIM_MODEL": "none",  # Change if your sim needs a specific model
            "PX4_SYS_AUTOSTART": "4001",  # X500 quadcopter
            # Add more vars as needed
        }

    # ========================================================================
    # OPTIONAL METHODS (override only if needed)
    # ========================================================================

    def get_default_world(self) -> str:
        """
        Override to change default world name.
        Base class returns "default".
        """
        return super().get_default_world()

    def get_available_worlds(self) -> List[str]:
        """
        Override to list available worlds for your simulator.
        Base class returns ["default"].
        """
        # TODO: Uncomment and modify if you have custom worlds
        # return ["default", "world1", "world2", "city", "forest"]
        return super().get_available_worlds()

    def validate_world(self, world_name: str) -> Tuple[bool, str]:
        """
        Override to add custom world validation logic.
        Base class checks if world is in get_available_worlds().
        """
        # TODO: Add custom validation if needed
        # Example: Check if world file exists
        # world_path = self.config_dir / "worlds" / f"{world_name}.world"
        # if not world_path.exists():
        #     return False, f"World file not found: {world_path}"
        return super().validate_world(world_name)

    def get_world_launch_info(self, world_name: str) -> Dict[str, str]:
        """
        Override to provide world-specific launch info.
        Base class returns basic info.
        """
        return super().get_world_launch_info(world_name)

    def launch_debug_translator(self, drones: List[DroneConfig]) -> bool:
        """
        Override to launch custom debug visualization nodes.

        Base class doesn't implement this - it's completely simulator-specific.
        You need to launch ally_visualizer and any simulator-specific enemy visualizers.

        Return True if successful, False otherwise.
        """
        # TODO: Implement debug visualization if needed
        print(f"[{self.get_name()}] Debug visualization not implemented yet")
        return True

    def cleanup(self) -> bool:
        """
        Override to add simulator-specific cleanup.

        IMPORTANT: Always call super().cleanup() to clean tracked processes.
        Then add any extra cleanup (pkill, config reset, etc.).
        """
        # Call base cleanup for tracked processes
        success = super().cleanup()

        # TODO: Add simulator-specific cleanup
        # Example: Kill remaining simulator processes
        # try:
        #     subprocess.run(["pkill", "-f", "mysim"], timeout=5)
        # except Exception as e:
        #     print(f"[{self.get_name()}] Error during cleanup: {e}")
        #     success = False

        return success

    def get_required_packages(self) -> List[str]:
        """
        Override to specify required ROS2 packages.
        Base class returns empty list.
        """
        # TODO: List your ROS2 packages
        # return ["my_camera_bridge", "my_odometry_bridge"]
        return super().get_required_packages()

    def get_documentation_url(self) -> str:
        """
        Override to link to your simulator's docs.
        Base class returns None.
        """
        # TODO: Update path
        # return "simulation/mysim/README.md"
        return super().get_documentation_url()

    def supports_feature(self, feature: str) -> bool:
        """
        Override to specify supported features.
        Base class returns False for all.

        Common features:
        - "rgb_camera", "depth_camera", "lidar"
        - "gpu_acceleration", "headless"
        - "photo_realistic", "fast_simulation"
        """
        # TODO: Uncomment and modify
        # supported = {
        #     "rgb_camera",
        #     "depth_camera",
        #     "gpu_acceleration",
        # }
        # return feature in supported
        return super().supports_feature(feature)


# ============================================================================
# REGISTER ENGINE (REQUIRED)
# ============================================================================

# TODO: Register your engine with the factory
# First parameter: Name used in CLI (./scripts/launch.sh --sim <this_name>)
# Second parameter: Your engine class
SimulationEngineFactory.register_engine("mysim", MySimEngine)  # TODO: Change "mysim" to your sim name
