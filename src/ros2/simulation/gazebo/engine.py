#!/usr/bin/env python3
"""
Gazebo Simulation Engine Implementation

Implements the SimulationEngine interface for Gazebo Harmonic simulator.
Gazebo is fast, lightweight, and great for development and CI/CD.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "common" / "base"))
from engine_base import SimulationEngineBase

sys.path.insert(0, str(Path(__file__).parent.parent / "common" / "interfaces"))
from sim_engine import DroneConfig, SimulationEngineFactory


class GazeboEngine(SimulationEngineBase):
    """Gazebo Harmonic simulation engine"""

    # Gazebo-specific configuration
    DEFAULT_WORLD = "default"
    AVAILABLE_WORLDS = [
        "default", "baylands", "forest", "lawn", "windy",
        "aruco", "frictionless", "kthspacelab", "moving_platform",
        "rover", "underwater", "walls"
    ]

    def get_name(self) -> str:
        return "Gazebo Harmonic"

    def get_default_world(self) -> str:
        """Return Gazebo's default world"""
        return self.DEFAULT_WORLD

    def get_available_worlds(self) -> List[str]:
        """Return list of available Gazebo worlds"""
        return self.AVAILABLE_WORLDS.copy()

    def validate_world(self, world_name: str) -> Tuple[bool, str]:
        """Validate if a Gazebo world is available"""
        if world_name not in self.AVAILABLE_WORLDS:
            return False, (
                f"Unknown world '{world_name}'. "
                f"Available: {', '.join(self.AVAILABLE_WORLDS)}"
            )

        # Check if world file actually exists in PX4
        world_path = self.px4_dir / "Tools" / "simulation" / "gz" / "worlds" / f"{world_name}.sdf"
        if world_path.exists():
            return True, f"World '{world_name}' is available"
        else:
            return False, f"World '{world_name}' not found at {world_path}"

    def get_world_launch_info(self, world_name: str) -> Dict[str, str]:
        """Return info for launching this Gazebo world"""
        return {
            "type": "gazebo",
            "world_name": world_name,
            "requires_manual_launch": False
        }

    def validate_installation(self) -> Tuple[bool, str]:
        """Check if Gazebo and ros_gz are installed"""
        # Check for gz command
        try:
            result = subprocess.run(
                ["gz", "sim", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False, "Gazebo 'gz' command not found or failed"
        except FileNotFoundError:
            return False, "Gazebo not installed. Install with: sudo apt install gz-harmonic"
        except subprocess.TimeoutExpired:
            return False, "Gazebo command timed out"

        # Check for PX4
        if not self.px4_dir.exists():
            return False, f"PX4-Autopilot not found at {self.px4_dir}"

        px4_binary = self.px4_dir / "build" / "px4_sitl_default" / "bin" / "px4"
        if not px4_binary.exists():
            return False, (
                f"PX4 not built. Run: cd {self.px4_dir} && "
                "make px4_sitl gz_x500_mono_cam"
            )

        # Check for ros_gz_bridge
        try:
            result = subprocess.run(
                ["ros2", "pkg", "prefix", "ros_gz_bridge"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False, "ros_gz_bridge package not found. Run: ./setup.sh --gazebo"
        except subprocess.TimeoutExpired:
            return False, "ROS2 command timed out"

        return True, "Gazebo installation validated successfully"

    def get_camera_topic(self, drone_name: str = "Ally") -> str:
        """Gazebo publishes camera to /camera/image"""
        return "/camera/image"

    def get_px4_connection_config(self, instance_id: int) -> Dict:
        """
        Gazebo uses UDP for MAVLink.
        Default port: 14560 + instance_id
        """
        return {
            "protocol": "udp",
            "port": 14560 + instance_id,
            "address": "localhost"
        }

    def _prompt_world_selection(self) -> str:
        """Interactively prompt user to select Gazebo world"""
        available = self.get_available_worlds()

        print(f"\n[{self.get_name()}] Available worlds:")
        for i, world in enumerate(available, 1):
            if world == self.DEFAULT_WORLD:
                print(f"  {i}. {world} (default)")
            else:
                print(f"  {i}. {world}")

        while True:
            choice = input(f"\n[{self.get_name()}] Select world (1-{len(available)}, or Enter for default): ").strip()

            if not choice:  # Enter pressed - use default
                return self.DEFAULT_WORLD

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(available):
                    return available[idx]
                else:
                    print(f"[{self.get_name()}] Invalid choice. Enter a number between 1 and {len(available)}")
            except ValueError:
                print(f"[{self.get_name()}] Invalid input. Enter a number or press Enter for default")

    def launch_simulator(self) -> bool:
        """
        Prepare Gazebo launch configuration.

        For Gazebo, PX4 automatically starts Gazebo, so we just need to
        select the world and store it for use in get_px4_env_vars().
        """
        # Interactive world selection
        self.selected_world = self._prompt_world_selection()

        print(f"\n[{self.get_name()}] Selected world: {self.selected_world}")
        print(f"[{self.get_name()}] Gazebo will be launched by PX4")
        return True

    def launch_bridges(self) -> bool:
        """
        Launch ros_gz_bridge for camera topics in terminal.

        Bridges Gazebo topics to ROS2:
        - /camera/image (Gazebo) -> /camera/image (ROS2)
        - /camera/camera_info (Gazebo) -> /camera/camera_info (ROS2)
        """
        print(f"[{self.get_name()}] Launching ROS2 bridges...")

        # Source ROS2 workspace
        ws_setup = self.ws_ros2 / "install" / "setup.bash"
        if not ws_setup.exists():
            print(f"[{self.get_name()}] ERROR: Workspace not built at {ws_setup}")
            return False

        # Get the selected world (or default if not set)
        world_name = getattr(self, 'selected_world', self.DEFAULT_WORLD)

        # Launch camera bridge
        # Bridge Gazebo camera topics to ROS2 with remapping
        # Gazebo publishes to: /world/{world_name}/model/x500_mono_cam_0/link/camera_link/sensor/imager/*
        # We remap to: /camera/*
        bridge_cmd = [
            "bash", "-c",
            f"source /opt/ros/humble/setup.bash && "
            f"source {ws_setup} && "
            f"ros2 run ros_gz_bridge parameter_bridge "
            f"/world/{world_name}/model/x500_mono_cam_0/link/camera_link/sensor/imager/image@sensor_msgs/msg/Image[gz.msgs.Image "
            f"/world/{world_name}/model/x500_mono_cam_0/link/camera_link/sensor/imager/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo "
            f"--ros-args "
            f"-r /world/{world_name}/model/x500_mono_cam_0/link/camera_link/sensor/imager/image:=/camera/image "
            f"-r /world/{world_name}/model/x500_mono_cam_0/link/camera_link/sensor/imager/camera_info:=/camera/camera_info"
        ]

        proc = self._launch_in_terminal(
            title="Gazebo Camera Bridge",
            cmd=bridge_cmd,
            color="green"
        )

        if proc:
            self.processes.append(("camera_bridge", proc))
            print(f"[{self.get_name()}] ✓ Camera bridge launched successfully")
            time.sleep(2)  # Give bridge time to start
            return True
        else:
            print(f"[{self.get_name()}] ERROR: Failed to launch camera bridge")
            return False

    def launch_debug_translator(self, drones: List[DroneConfig]) -> bool:
        """
        Launch visualization nodes for Gazebo multi-drone visualization.

        In Gazebo, both PX4 instances report local positions (0,0,0).
        The enemy visualizer ADDS an offset to the enemy drone's position
        so both drones appear in correct global positions in RViz.
        """
        print(f"[{self.get_name()}] Launching visualization nodes...")

        ws_setup = self.ws_ros2 / "install" / "setup.bash"

        # Launch ally visualizer (always)
        ally_cmd = [
            "bash", "-c",
            f"source /opt/ros/humble/setup.bash && "
            f"source {ws_setup} && "
            f"ros2 run ally_visualizer ally_visualizer"
        ]

        ally_proc = self._launch_in_terminal(
            title="Ally Visualizer",
            cmd=ally_cmd,
            color="green"
        )

        if not ally_proc:
            print(f"[{self.get_name()}] WARNING: Failed to start ally visualizer")
            return False

        self.processes.append(("ally_visualizer", ally_proc))
        print(f"[{self.get_name()}] ✓ Ally visualizer started")

        # Launch enemy visualizer (if multi-drone)
        enemy_offset_x = 0.0
        enemy_offset_y = 0.0
        enemy_offset_z = 0.0

        for drone in drones:
            if drone.instance_id == 1:  # Enemy drone
                # Pass position coordinates directly (no NED->ENU conversion)
                enemy_offset_x = drone.position[0]
                enemy_offset_y = drone.position[1]
                enemy_offset_z = drone.position[2]

                # Build enemy visualizer command with offset parameters
                enemy_cmd = [
                    "bash", "-c",
                    f"source /opt/ros/humble/setup.bash && "
                    f"source {ws_setup} && "
                    f"ros2 run gazebo_enemy_visualizer enemy_visualizer "
                    f"--ros-args "
                    f"-p enemy_offset_x:={enemy_offset_x} "
                    f"-p enemy_offset_y:={enemy_offset_y} "
                    f"-p enemy_offset_z:={enemy_offset_z}"
                ]

                enemy_proc = self._launch_in_terminal(
                    title="Enemy Visualizer (Gazebo)",
                    cmd=enemy_cmd,
                    color="red"
                )

                if not enemy_proc:
                    print(f"[{self.get_name()}] WARNING: Failed to start enemy visualizer")
                    return False

                self.processes.append(("enemy_visualizer", enemy_proc))
                print(f"[{self.get_name()}] ✓ Enemy visualizer started")
                print(f"[{self.get_name()}]   Enemy offset: x={enemy_offset_x}, y={enemy_offset_y}, z={enemy_offset_z}")
                break

        return True

    def get_px4_env_vars(self, drone_config: DroneConfig) -> Dict[str, str]:
        """
        Get environment variables for PX4 when using Gazebo.
        """
        # Use selected world from launch_simulator()
        world_name = getattr(self, 'selected_world', self.DEFAULT_WORLD)

        env = {
            # PX4 Gazebo model
            "PX4_SIM_MODEL": "gz_x500_mono_cam" if drone_config.has_camera else "gz_x500",

            # Gazebo simulation engine
            "PX4_GZ_SIM_RENDER_ENGINE": "ogre2",

            # Instance-specific settings
            "PX4_SYS_AUTOSTART": "4001",  # X500 quadcopter

            # Position
            "PX4_GZ_MODEL_POSE": f"{drone_config.position[0]},{drone_config.position[1]},"
                                  f"{drone_config.position[2]},0,0,{drone_config.yaw}",

            # World name (PX4 will find it in PX4_GZ_WORLDS from gz_env.sh)
            "PX4_GZ_WORLD": world_name,
        }

        # Second drone should NOT launch Gazebo (standalone mode)
        # First drone (instance 0) launches Gazebo, others attach to existing world
        if drone_config.instance_id > 0:
            env["PX4_GZ_STANDALONE"] = "1"

        # Software rendering for headless/WSL environments
        if os.environ.get("DISPLAY") is None or os.environ.get("WSL_DISTRO_NAME"):
            env["LIBGL_ALWAYS_SOFTWARE"] = "1"

        return env

    def cleanup(self) -> bool:
        """Clean up Gazebo processes"""
        # Call base cleanup for tracked processes
        success = super().cleanup()

        # Kill any remaining Gazebo/PX4 processes
        try:
            subprocess.run(["pkill", "-f", "gz sim"], timeout=5)
            subprocess.run(["pkill", "-f", "px4"], timeout=5)
            subprocess.run(["pkill", "-f", "ros_gz_bridge"], timeout=5)
        except Exception as e:
            print(f"[{self.get_name()}] Error during pkill: {e}")
            success = False

        return success

    def get_required_packages(self) -> List[str]:
        """ROS2 packages needed for Gazebo"""
        return [
            "ros_gz_bridge",
            "ros_gz_sim",
            "ros_gz_image"
        ]

    def get_documentation_url(self) -> str:
        """Link to Gazebo docs"""
        return "simulation/gazebo/README.md"

    def supports_feature(self, feature: str) -> bool:
        """Check Gazebo feature support"""
        supported = {
            "rgb_camera",
            "depth_camera",
            "lidar",
            "imu",
            "gps",
            "fast_simulation",
            "headless"
        }
        return feature in supported


# Register this engine with the factory
SimulationEngineFactory.register_engine("gazebo", GazeboEngine)
