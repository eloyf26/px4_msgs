#!/usr/bin/env python3
"""
AirSim Simulation Engine Implementation

Implements the SimulationEngine interface for Microsoft AirSim (Unreal Engine).
AirSim provides photo-realistic rendering and is great for computer vision research.
"""

import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "common" / "base"))
from engine_base import SimulationEngineBase

sys.path.insert(0, str(Path(__file__).parent.parent / "common" / "interfaces"))
from sim_engine import DroneConfig, SimulationEngineFactory, SimulationMode


class AirSimEngine(SimulationEngineBase):
    """Microsoft AirSim simulation engine"""

    # AirSim-specific configuration
    DEFAULT_WORLD = "blocks"

    # Mapping: friendly_name -> (directory, script_name)
    ENVIRONMENT_MAP = {
        "blocks": ("LinuxBlocks1.8.1", "Blocks.sh"),
        "landscape": ("LandscapeMountains", "LandscapeMountains.sh"),
        "airsimnh": ("AirSimNH", "AirSimNH.sh"),  # Small urban neighborhood
    }

    # Download URLs for AirSim environments
    # Note: v1.8.1 has Blocks, v1.7.0-linux has LandscapeMountains and AirSimNH
    ENVIRONMENT_DOWNLOAD_URLS = {
        "blocks": "https://github.com/microsoft/AirSim/releases/download/v1.8.1/Blocks.zip",
        "landscape": "https://github.com/microsoft/AirSim/releases/download/v1.7.0-linux/LandscapeMountains.zip",
        "airsimnh": "https://github.com/microsoft/AirSim/releases/download/v1.7.0-linux/AirSimNH.zip",
    }

    def __init__(self, config):
        super().__init__(config)
        self.config_dir = self.repo_root / "src" / "ros2" / "simulation" / "airsim" / "config"
        self.airsim_user_config = Path.home() / "Documents" / "AirSim" / "settings.json"

    def get_name(self) -> str:
        return "AirSim"

    def get_default_world(self) -> str:
        """Return AirSim's default environment"""
        return self.DEFAULT_WORLD

    def get_available_worlds(self) -> List[str]:
        """Return list of available AirSim environments"""
        return list(self.ENVIRONMENT_MAP.keys())

    def validate_world(self, world_name: str) -> Tuple[bool, str]:
        """Validate if an AirSim environment is available"""
        if world_name not in self.ENVIRONMENT_MAP:
            return False, (
                f"Unknown environment '{world_name}'. "
                f"Available: {', '.join(self.get_available_worlds())}"
            )

        # Check if environment is actually installed
        dir_name, script = self.ENVIRONMENT_MAP[world_name]
        env_path = Path.home() / "AirSimEnvironments" / dir_name / "LinuxNoEditor"
        script_path = env_path / script

        if env_path.exists() and script_path.exists():
            return True, f"Environment '{world_name}' is installed at {env_path}"
        else:
            return False, (
                f"Environment '{world_name}' not installed. "
                f"Expected at {env_path}"
            )

    def get_world_launch_info(self, world_name: str) -> Dict[str, str]:
        """Return info for launching this AirSim environment"""
        dir_name, script = self.ENVIRONMENT_MAP[world_name]
        env_path = Path.home() / "AirSimEnvironments" / dir_name / "LinuxNoEditor"

        return {
            "type": "airsim",
            "environment_name": world_name,
            "directory": str(env_path),
            "script": script,
            "requires_manual_launch": True
        }

    def validate_installation(self) -> Tuple[bool, str]:
        """Check if AirSim Python API and packages are installed"""

        # Check for AirSim Python package
        try:
            import airsim
        except ImportError:
            return False, (
                "AirSim Python package not installed. "
                "Run: pip install airsim msgpack-rpc-python"
            )

        # Check for PX4
        if not self.px4_dir.exists():
            return False, f"PX4-Autopilot not found at {self.px4_dir}"

        px4_binary = self.px4_dir / "build" / "px4_sitl_default" / "bin" / "px4"
        if not px4_binary.exists():
            return False, (
                f"PX4 not built. Run: cd {self.px4_dir} && "
                "make px4_sitl_default"
            )

        # Check for camera_bridge
        try:
            result = subprocess.run(
                ["ros2", "pkg", "prefix", "camera_bridge"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False, (
                    "camera_bridge package not found. "
                    "Run: ./setup.sh --airsim"
                )
        except subprocess.TimeoutExpired:
            return False, "ROS2 command timed out"

        # Check for AirSim environment
        if not self._check_airsim_env():
            return False, (
                "No AirSim environment detected. "
                "Run: ./scripts/install_airsim_env.sh --blocks"
            )

        return True, "AirSim installation validated successfully"

    def _check_airsim_env(self) -> bool:
        """Check if at least one AirSim environment is installed"""
        env_dir = Path.home() / "AirSimEnvironments"
        if not env_dir.exists():
            return False

        # Check for common environments
        common_envs = ["Blocks", "LinuxBlocks1.8.1", "LandscapeMountains", "City"]
        for env in common_envs:
            if (env_dir / env).exists():
                return True

        return False

    def _download_and_install_environment(self, env_name: str) -> bool:
        """
        Download and install an AirSim environment.

        Args:
            env_name: Environment name (blocks, landscape, city)

        Returns:
            True if successful, False otherwise
        """
        if env_name not in self.ENVIRONMENT_DOWNLOAD_URLS:
            print(f"[{self.get_name()}] ERROR: Unknown environment '{env_name}'")
            return False

        url = self.ENVIRONMENT_DOWNLOAD_URLS[env_name]
        dir_name, script = self.ENVIRONMENT_MAP[env_name]
        env_dir = Path.home() / "AirSimEnvironments"
        target_dir = env_dir / dir_name

        # Environment metadata
        env_sizes = {
            "blocks": "~400MB",
            "landscape": "~5GB",
            "airsimnh": "~1.5GB"
        }

        print(f"\n[{self.get_name()}] ═══════════════════════════════════════")
        print(f"[{self.get_name()}] Downloading {env_name.upper()} environment")
        print(f"[{self.get_name()}] Size: {env_sizes.get(env_name, 'Unknown')}")
        print(f"[{self.get_name()}] URL: {url}")
        print(f"[{self.get_name()}] ═══════════════════════════════════════\n")

        zip_file = None  # Initialize for cleanup in exception handler

        try:
            # Create directory
            env_dir.mkdir(parents=True, exist_ok=True)

            # Check if already exists
            if target_dir.exists():
                print(f"[{self.get_name()}] WARNING: {dir_name} already exists")
                response = input(f"[{self.get_name()}] Re-download? (y/N): ").strip().lower()
                if response != 'y':
                    print(f"[{self.get_name()}] Using existing installation")
                    return True

                # Remove existing
                import shutil
                shutil.rmtree(target_dir)
                print(f"[{self.get_name()}] Removed existing installation")

            # Download
            zip_file = env_dir / f"{env_name}.zip"
            print(f"[{self.get_name()}] Downloading... (this may take a while)")

            result = subprocess.run(
                ["wget", "--progress=bar:force", "-O", str(zip_file), url],
                cwd=str(env_dir),
                check=True
            )

            if not zip_file.exists():
                print(f"[{self.get_name()}] ERROR: Download failed")
                return False

            print(f"[{self.get_name()}] ✓ Download complete")

            # Extract
            print(f"[{self.get_name()}] Extracting environment...")
            result = subprocess.run(
                ["unzip", "-q", str(zip_file)],
                cwd=str(env_dir),
                check=True
            )

            # Remove zip file
            zip_file.unlink()
            print(f"[{self.get_name()}] ✓ Extraction complete")

            # Make script executable
            script_path = target_dir / "LinuxNoEditor" / script
            if script_path.exists():
                os.chmod(script_path, 0o755)
                print(f"[{self.get_name()}] ✓ Made script executable")
            else:
                print(f"[{self.get_name()}] WARNING: Script not found at {script_path}")
                return False

            # Verify installation
            if script_path.exists() and os.access(script_path, os.X_OK):
                print(f"\n[{self.get_name()}] ╔════════════════════════════════════════╗")
                print(f"[{self.get_name()}] ║  Installation Successful!              ║")
                print(f"[{self.get_name()}] ╚════════════════════════════════════════╝")
                print(f"[{self.get_name()}] Environment: {target_dir}")
                print(f"[{self.get_name()}] Launch script: {script_path}\n")
                return True
            else:
                print(f"[{self.get_name()}] ERROR: Installation verification failed")
                return False

        except subprocess.CalledProcessError as e:
            print(f"[{self.get_name()}] ERROR: Command failed: {e}")
            # Clean up partial download
            if zip_file and zip_file.exists():
                zip_file.unlink()
            return False
        except Exception as e:
            print(f"[{self.get_name()}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_camera_topic(self, drone_name: str = "Ally") -> str:
        """AirSim camera bridge publishes to /camera/image"""
        return "/camera/image"

    def get_px4_connection_config(self, instance_id: int) -> Dict:
        """
        AirSim uses TCP for MAVLink (LockStep mode).
        Default port: 4560 for first drone
        """
        return {
            "protocol": "tcp",
            "port": 4560,  # AirSim uses fixed port 4560 for PX4
            "address": "localhost"
        }

    def _prompt_world_selection(self) -> str:
        """Interactively prompt user to select AirSim environment"""
        available = self.get_available_worlds()

        print(f"\n[{self.get_name()}] Available environments:")
        for i, world in enumerate(available, 1):
            # Check if installed
            dir_name, script = self.ENVIRONMENT_MAP[world]
            env_path = Path.home() / "AirSimEnvironments" / dir_name / "LinuxNoEditor"
            script_path = env_path / script

            is_installed = env_path.exists() and script_path.exists()
            status = "✓ installed" if is_installed else "✗ not installed"

            if world == self.get_default_world():
                print(f"  {i}. {world} (default) [{status}]")
            else:
                print(f"  {i}. {world} [{status}]")

        while True:
            choice = input(f"\n[{self.get_name()}] Select environment (1-{len(available)}, or Enter for default): ").strip()

            if not choice:  # Enter pressed - use default
                return self.get_default_world()

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(available):
                    selected = available[idx]
                    # Validate it's installed
                    is_valid, msg = self.validate_world(selected)
                    if is_valid:
                        return selected
                    else:
                        # Environment not installed - offer to download
                        print(f"[{self.get_name()}] {msg}")
                        response = input(f"[{self.get_name()}] Download and install now? (y/n): ").strip().lower()

                        if response == 'y':
                            # Attempt download and installation
                            if self._download_and_install_environment(selected):
                                print(f"[{self.get_name()}] ✓ Environment ready!")
                                return selected
                            else:
                                print(f"[{self.get_name()}] ERROR: Installation failed")
                                print(f"[{self.get_name()}] Please select a different environment or try again later")
                        else:
                            print(f"[{self.get_name()}] Please select an installed environment")
                else:
                    print(f"[{self.get_name()}] Invalid choice. Enter a number between 1 and {len(available)}")
            except ValueError:
                print(f"[{self.get_name()}] Invalid input. Enter a number or press Enter for default")

    def launch_simulator(self) -> bool:
        """
        Launch AirSim environment automatically.
        Prompts user to select environment, then launches it in a new terminal.
        """
        print(f"[{self.get_name()}] Preparing AirSim configuration...")

        # Ensure settings.json is in the correct location
        if not self._setup_config():
            return False

        # Interactive world selection
        selected_world = self._prompt_world_selection()
        world_info = self.get_world_launch_info(selected_world)

        print(f"\n[{self.get_name()}] Selected environment: {world_info['environment_name']}")
        print(f"[{self.get_name()}] Launching AirSim...")

        # Auto-launch AirSim in new terminal
        airsim_cmd = [
            "bash", "-c",
            f"cd {world_info['directory']} && ./{world_info['script']}"
        ]

        proc = self._launch_in_terminal(
            title=f"AirSim - {world_info['environment_name']}",
            cmd=airsim_cmd,
            color="blue"
        )

        if not proc:
            print(f"[{self.get_name()}] ERROR: Failed to launch AirSim")
            return False

        self.processes.append(("airsim_simulator", proc))
        print(f"[{self.get_name()}] ✓ AirSim launched in new terminal")
        print(f"[{self.get_name()}] Waiting for Unreal Engine to initialize...")
        time.sleep(10)  # Give Unreal Engine time to start

        # Verify connection to AirSim (with longer timeout for Unreal startup)
        print(f"[{self.get_name()}] Connecting to AirSim API...")
        if not self._verify_airsim_connection(timeout=30):
            print(f"[{self.get_name()}] ERROR: Could not connect to AirSim after 30 seconds")
            print(f"[{self.get_name()}]        Check the AirSim terminal window for errors")
            return False

        print(f"[{self.get_name()}] ✓ Successfully connected to AirSim")
        return True

    def _setup_config(self) -> bool:
        """Generate settings.json from template with drone positions"""
        try:
            # Create AirSim directory if it doesn't exist
            self.airsim_user_config.parent.mkdir(parents=True, exist_ok=True)

            # Determine which template to use based on mode
            if self.config.mode == SimulationMode.MULTI_DRONE:
                template_file = self.config_dir / "settings_template_multi.json"
            else:
                template_file = self.config_dir / "settings_template_single.json"

            # Fallback to static config if template doesn't exist
            if not template_file.exists():
                print(f"[{self.get_name()}] WARNING: Template not found at {template_file}")
                print(f"[{self.get_name()}]          Falling back to static settings.json")
                config_file = self.config_dir / "settings.json"
                if not config_file.exists():
                    print(f"[{self.get_name()}] ERROR: Config not found at {config_file}")
                    return False

                import shutil
                shutil.copy(config_file, self.airsim_user_config)
                print(f"[{self.get_name()}] Copied static {config_file.name}")
                return True

            # Load template
            with open(template_file, 'r') as f:
                template = f.read()

            # Find Ally drone config
            ally = next((d for d in self.config.drones if d.name == "Ally"), None)
            if not ally:
                print(f"[{self.get_name()}] ERROR: No Ally drone in configuration")
                return False

            # Substitute Ally position
            config_content = template.replace("{{ALLY_X}}", str(ally.position[0]))
            config_content = config_content.replace("{{ALLY_Y}}", str(ally.position[1]))
            config_content = config_content.replace("{{ALLY_Z}}", str(ally.position[2]))
            config_content = config_content.replace("{{ALLY_YAW}}", str(ally.yaw))

            # Substitute Enemy position if multi-drone
            if self.config.mode == SimulationMode.MULTI_DRONE:
                enemy = next((d for d in self.config.drones if d.name == "Enemy"), None)
                if enemy:
                    config_content = config_content.replace("{{ENEMY_X}}", str(enemy.position[0]))
                    config_content = config_content.replace("{{ENEMY_Y}}", str(enemy.position[1]))
                    config_content = config_content.replace("{{ENEMY_Z}}", str(enemy.position[2]))
                    config_content = config_content.replace("{{ENEMY_YAW}}", str(enemy.yaw))
                else:
                    print(f"[{self.get_name()}] WARNING: Multi-drone mode but no Enemy config found")

            # Backup existing config
            if self.airsim_user_config.exists():
                backup = self.airsim_user_config.with_suffix(
                    f".backup.{int(time.time())}.json"
                )
                self.airsim_user_config.rename(backup)
                print(f"[{self.get_name()}] Backed up existing config to {backup}")

            # Write generated config
            with open(self.airsim_user_config, 'w') as f:
                f.write(config_content)

            print(f"[{self.get_name()}] Generated settings.json from {template_file.name}")
            print(f"[{self.get_name()}]   Ally position: ({ally.position[0]}, {ally.position[1]}, {ally.position[2]}) yaw={ally.yaw}")
            if self.config.mode == SimulationMode.MULTI_DRONE and enemy:
                print(f"[{self.get_name()}]   Enemy position: ({enemy.position[0]}, {enemy.position[1]}, {enemy.position[2]}) yaw={enemy.yaw}")

            return True

        except Exception as e:
            print(f"[{self.get_name()}] Error setting up config: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _verify_airsim_connection(self, timeout: int = 10) -> bool:
        """Verify we can connect to AirSim API"""
        try:
            import airsim

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    client = airsim.MultirotorClient()
                    client.confirmConnection()
                    return True
                except:
                    time.sleep(1)

            return False

        except Exception as e:
            print(f"[{self.get_name()}] Connection error: {e}")
            return False

    def launch_bridges(self) -> bool:
        """
        Launch AirSim ROS2 camera bridge.
        """
        print(f"[{self.get_name()}] Launching ROS2 bridges...")

        # Source ROS2 workspace
        ws_setup = self.ws_ros2 / "install" / "setup.bash"
        if not ws_setup.exists():
            print(f"[{self.get_name()}] ERROR: Workspace not built at {ws_setup}")
            return False

        # Launch camera bridge
        camera_cmd = [
            "bash", "-c",
            f"source /opt/ros/humble/setup.bash && "
            f"source {ws_setup} && "
            f"ros2 run camera_bridge camera_bridge"
        ]

        proc = self._launch_in_terminal(
            title="AirSim Camera Bridge",
            cmd=camera_cmd,
            color="green"
        )

        if proc:
            self.processes.append(("camera_bridge", proc))
            print(f"[{self.get_name()}] ✓ Camera bridge launched successfully")
            time.sleep(2)
        else:
            print(f"[{self.get_name()}] ERROR: Failed to launch camera bridge")
            return False

        return True

    def get_px4_env_vars(self, drone_config: DroneConfig) -> Dict[str, str]:
        """
        Get environment variables for PX4 when using AirSim.
        """
        return {
            # Tell PX4 to use AirSim simulator (not Gazebo)
            "PX4_SIMULATOR": "airsim",
            "PX4_SIM_MODEL": "iris",

            # Instance-specific settings
            "PX4_SYS_AUTOSTART": "10016",  # Generic quadcopter for AirSim

            # AirSim uses TCP, not UDP
            "PX4_SIM_HOST": "localhost",
        }

    def launch_debug_translator(self, drones: List[DroneConfig]) -> bool:
        """
        Launch visualization nodes for AirSim multi-drone visualization.

        In AirSim, enemy position comes from AirSim API (global position).
        The enemy visualizer SUBTRACTS ally spawn offset to align with PX4 frame.
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
        ally_offset_x = 0.0
        ally_offset_y = 0.0
        ally_offset_z = 0.0

        for drone in drones:
            if drone.instance_id == 1:  # Enemy drone
                # Get ally offset for reference frame conversion
                # simGetObjectPose returns global AirSim positions, subtract ally offset to get PX4 local frame
                ally = next((d for d in drones if d.name == "Ally"), None)
                if ally:
                    ally_offset_x = ally.position[0]
                    ally_offset_y = ally.position[1]
                    ally_offset_z = ally.position[2]

                # Build enemy visualizer command with ally offset
                # AirSim enemy visualizer uses simGetObjectPose (global) and subtracts ally offset
                enemy_cmd = [
                    "bash", "-c",
                    f"source /opt/ros/humble/setup.bash && "
                    f"source {ws_setup} && "
                    f"ros2 run airsim_enemy_visualizer enemy_visualizer "
                    f"--ros-args "
                    f"-p ally_offset_x:={ally_offset_x} "
                    f"-p ally_offset_y:={ally_offset_y} "
                    f"-p ally_offset_z:={ally_offset_z}"
                ]

                enemy_proc = self._launch_in_terminal(
                    title="Enemy Visualizer (AirSim)",
                    cmd=enemy_cmd,
                    color="red"
                )

                if not enemy_proc:
                    print(f"[{self.get_name()}] WARNING: Failed to start enemy visualizer")
                    return False

                self.processes.append(("enemy_visualizer", enemy_proc))
                print(f"[{self.get_name()}] ✓ Enemy visualizer started")
                print(f"[{self.get_name()}]   Ally offset (for frame conversion): x={ally_offset_x}, y={ally_offset_y}, z={ally_offset_z}")
                break

        return True

    def cleanup(self) -> bool:
        """Clean up AirSim processes"""
        # Call base cleanup for tracked processes
        success = super().cleanup()

        # Kill any remaining AirSim bridge processes
        try:
            subprocess.run(["pkill", "-f", "camera_bridge"], timeout=5)
            subprocess.run(["pkill", "-f", "viz_translator"], timeout=5)
            subprocess.run(["pkill", "-f", "px4"], timeout=5)
        except Exception as e:
            print(f"[{self.get_name()}] Error during pkill: {e}")
            success = False

        print(f"[{self.get_name()}] Note: AirSim environment must be closed manually")
        return success

    def get_required_packages(self) -> List[str]:
        """ROS2 packages needed for AirSim"""
        return [
            "camera_bridge",
            "viz_translator"
        ]

    def get_documentation_url(self) -> str:
        """Link to AirSim docs"""
        return "simulation/airsim/README.md"

    def supports_feature(self, feature: str) -> bool:
        """Check AirSim feature support"""
        supported = {
            "rgb_camera",
            "depth_camera",
            "segmentation",
            "photo_realistic",
            "gpu_acceleration",
            "unreal_engine",
            "weather_effects"
        }
        return feature in supported


# Register this engine with the factory
SimulationEngineFactory.register_engine("airsim", AirSimEngine)
