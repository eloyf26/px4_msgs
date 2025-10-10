#!/usr/bin/env python3
"""
Unified Halcon1 Simulation Launcher

This launcher provides a single entry point for all simulation environments.
It uses the simulation engine abstraction to support Gazebo, AirSim, Isaac Sim, etc.

Usage:
    ./simulation/common/launcher.py --sim gazebo
    ./simulation/common/launcher.py --sim airsim --debug
    ./simulation/common/launcher.py --sim gazebo --mode multi --debug
    ./simulation/common/launcher.py --sim gazebo --world custom_world
"""

import argparse
import subprocess
import sys
import time
import signal
from pathlib import Path
from typing import List, Optional

# Add interfaces to path
sys.path.insert(0, str(Path(__file__).parent / "interfaces"))
from sim_engine import (
    SimulationEngine,
    SimulationEngineFactory,
    SimulationConfig,
    SimulationMode,
    DroneConfig
)

# Import all engine implementations to register them
# Use importlib to avoid module name collisions (both named "engine.py")
import importlib.util

# Import Gazebo engine
gazebo_engine_path = Path(__file__).parent.parent / "gazebo" / "engine.py"
spec = importlib.util.spec_from_file_location("gazebo_engine_module", gazebo_engine_path)
gazebo_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gazebo_engine)

# Import AirSim engine
airsim_engine_path = Path(__file__).parent.parent / "airsim" / "engine.py"
spec = importlib.util.spec_from_file_location("airsim_engine_module", airsim_engine_path)
airsim_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(airsim_engine)


class Halcon1Launcher:
    """Main launcher for Halcon1 simulation system"""

    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent.parent.parent
        self.px4_dir = self.repo_root / "external" / "PX4-Autopilot"
        self.micro_xrce_agent = (
            self.repo_root / "external" / "Micro-XRCE-DDS-Agent" / "build" / "MicroXRCEAgent"
        )
        self.ws_ros2 = self.repo_root

        self.processes = []
        self.engine: Optional[SimulationEngine] = None

        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n[Launcher] Shutting down...")
        self.cleanup()
        sys.exit(0)

    def _detect_terminal(self) -> tuple:
        """
        Detect available terminal emulator.

        Returns:
            (command, supports_title): Tuple of terminal command and whether it supports --title
        """
        import shutil

        if shutil.which("gnome-terminal"):
            return ("gnome-terminal", True)
        elif shutil.which("xterm"):
            return ("xterm", True)
        elif shutil.which("konsole"):
            return ("konsole", True)
        elif shutil.which("terminator"):
            return ("terminator", True)
        else:
            print("[Launcher] WARNING: No terminal emulator found. Processes will run hidden.")
            print("[Launcher]          Install gnome-terminal: sudo apt install gnome-terminal")
            return (None, False)

    def _launch_in_terminal(self, title: str, cmd: list, color: str = "green", cwd: str = None) -> Optional[subprocess.Popen]:
        """
        Launch a process in a new terminal window.

        Args:
            title: Window title
            cmd: Command to execute as list
            color: Terminal header color (green, blue, red, yellow, cyan)
            cwd: Working directory (optional)

        Returns:
            Process handle or None if terminal not available
        """
        terminal, supports_title = self._detect_terminal()

        if not terminal:
            # Fallback: launch without terminal (output to stdout)
            print(f"[Launcher] WARNING: Launching '{title}' without terminal")
            try:
                proc = subprocess.Popen(cmd, cwd=cwd)
                return proc
            except Exception as e:
                print(f"[Launcher] ERROR: Failed to launch {title}: {e}")
                return None

        # Color codes for terminal header
        colors = {
            "green": "\\033[0;32m",
            "blue": "\\033[0;34m",
            "red": "\\033[0;31m",
            "yellow": "\\033[1;33m",
            "cyan": "\\033[0;36m",
            "nc": "\\033[0m"  # No color
        }

        color_code = colors.get(color, colors["green"])
        nc = colors["nc"]

        # Build the command string
        cmd_str = " ".join([f'"{arg}"' if " " in str(arg) else str(arg) for arg in cmd])

        # Build bash command with header and keep-alive
        bash_cmd = f"""
        echo -e '{color_code}====================================================={nc}';
        echo -e '{color_code}  {title}{nc}';
        echo -e '{color_code}====================================================={nc}';
        echo '';
        {cmd_str};
        EXIT_CODE=$?;
        echo '';
        echo -e '{color_code}====================================================={nc}';
        if [ $EXIT_CODE -eq 0 ]; then
            echo -e '{color_code}Process exited normally (code $EXIT_CODE){nc}';
        else
            echo -e '{colors["red"]}Process exited with error (code $EXIT_CODE){nc}';
        fi;
        echo -e '{color_code}Press Enter to close this window...{nc}';
        read;
        """

        # Build terminal command
        if terminal == "gnome-terminal":
            terminal_cmd = [
                terminal,
                "--title", title,
                "--",
                "bash", "-c", bash_cmd
            ]
        elif terminal == "xterm":
            terminal_cmd = [
                terminal,
                "-title", title,
                "-hold",
                "-e", "bash", "-c", bash_cmd
            ]
        elif terminal == "konsole":
            terminal_cmd = [
                terminal,
                "--new-tab",
                "--title", title,
                "-e", "bash", "-c", bash_cmd
            ]
        elif terminal == "terminator":
            terminal_cmd = [
                terminal,
                "--new-window",
                "--title", title,
                "-e", f"bash -c '{bash_cmd}'"
            ]

        # Launch terminal
        try:
            proc = subprocess.Popen(terminal_cmd, cwd=cwd)
            return proc
        except Exception as e:
            print(f"[Launcher] ERROR: Failed to launch terminal for {title}: {e}")
            return None

    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="Unified Halcon1 Simulation Launcher",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --sim gazebo
  %(prog)s --sim airsim --debug
  %(prog)s --sim gazebo --mode multi --debug

Available simulators:
  """ + ", ".join(SimulationEngineFactory.list_engines())
        )

        parser.add_argument(
            "--sim", "--simulator",
            dest="simulator",
            choices=SimulationEngineFactory.list_engines(),
            default="gazebo",
            help="Simulation engine to use (default: gazebo)"
        )

        parser.add_argument(
            "--mode",
            choices=["single", "multi", "hardware"],
            default="single",
            help="Simulation mode: single drone, multi-drone, or hardware (default: single)"
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug visualizers (ally_visualizer, enemy_visualizer for debug markers)"
        )

        parser.add_argument(
            "--separate-terminals",
            action="store_true",
            help="Launch detection, tracking, and guidance nodes in separate terminals"
        )

        parser.add_argument(
            "--skip-detection",
            action="store_true",
            help="Skip launching the detection node"
        )

        parser.add_argument(
            "--skip-tracking",
            action="store_true",
            help="Skip launching the tracking node"
        )

        parser.add_argument(
            "--skip-guidance",
            action="store_true",
            help="Skip launching the guidance node"
        )

        return parser.parse_args()

    def create_drone_configs(self, mode: SimulationMode) -> List[DroneConfig]:
        """Create drone configurations based on mode"""
        drones = []

        if mode == SimulationMode.SINGLE_DRONE:
            # Single ally drone
            drones.append(DroneConfig(
                name="Ally",
                instance_id=0,
                position=(0.0, 0.0, 0.0),
                yaw=0.0,
                has_camera=True
            ))

        elif mode == SimulationMode.MULTI_DRONE:
            # Ally drone with camera at origin
            drones.append(DroneConfig(
                name="Ally",
                instance_id=0,
                position=(0.0, 0.0, 0.0),
                yaw=0.0,
                has_camera=True
            ))

            # Enemy drone 5 meters North (NED X=5 becomes ENU Y=5 in Gazebo)
            # Both drones face same direction for easier debugging
            drones.append(DroneConfig(
                name="Enemy",
                instance_id=1,
                position=(5.0, 0.0, 0.0),  # NED coordinates: 5m North
                yaw=0.0,
                has_camera=False
            ))

        return drones

    def validate_environment(self) -> bool:
        """Validate that required components are installed"""
        print("[Launcher] Validating environment...")

        # Check PX4
        if not self.px4_dir.exists():
            print(f"[Launcher] ERROR: PX4 not found at {self.px4_dir}")
            return False

        # Check MicroXRCE Agent
        if not self.micro_xrce_agent.exists():
            print(f"[Launcher] ERROR: MicroXRCE Agent not found at {self.micro_xrce_agent}")
            print("[Launcher] Build it with: cd external/Micro-XRCE-DDS-Agent && mkdir build && cd build && cmake .. && make")
            return False

        # Check ROS2 workspace
        ws_setup = self.ws_ros2 / "install" / "setup.bash"
        if not ws_setup.exists():
            print(f"[Launcher] ERROR: ROS2 workspace not built at {self.ws_ros2}")
            print("[Launcher] Build it with: colcon build")
            return False

        print("[Launcher] ✓ Basic environment validated")
        return True

    def launch_microxrce_agents(self, num_drones: int) -> bool:
        """
        Launch single MicroXRCE-DDS agent (handles all PX4 instances).

        Note: One agent on port 8888 can handle multiple drones.
        """
        print("[Launcher] Starting MicroXRCE agent...")

        # Check if port 8888 is already in use
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(('', 8888))
            sock.close()
        except OSError:
            print("[Launcher] WARNING: Port 8888 already in use")
            print("[Launcher] Attempting to kill existing MicroXRCE agent...")
            try:
                subprocess.run(["pkill", "-f", "MicroXRCEAgent"], timeout=5)
                time.sleep(1)
                print("[Launcher] ✓ Killed existing agent")
            except Exception as e:
                print(f"[Launcher] WARNING: Could not kill existing agent: {e}")

        cmd = [str(self.micro_xrce_agent), "udp4", "-p", "8888"]

        proc = self._launch_in_terminal(
            title="MicroXRCE Agent (Port 8888)",
            cmd=cmd,
            color="green"
        )

        if proc:
            self.processes.append(("microxrce_agent", proc))
            print("[Launcher] ✓ MicroXRCE agent started on port 8888")
            time.sleep(2)  # Give agent time to start
            return True
        else:
            print("[Launcher] ERROR: Failed to start MicroXRCE agent")
            return False

    def launch_px4(self, drone_config: DroneConfig, env_vars: dict) -> bool:
        """Launch PX4 SITL instance in terminal"""
        print(f"[Launcher] Starting PX4 for {drone_config.name} (instance {drone_config.instance_id})...")

        # Build PX4 command
        px4_cmd = [
            str(self.px4_dir / "build" / "px4_sitl_default" / "bin" / "px4"),
            "-i", str(drone_config.instance_id),
            str(self.px4_dir / "build" / "px4_sitl_default" / "etc")
        ]

        # Prepare environment variables as exports for bash
        env_exports = []
        for key, value in env_vars.items():
            env_exports.append(f"export {key}='{value}'")

        # Add PX4_SIM_MODEL
        px4_sim_model = env_vars.get("PX4_SIM_MODEL", "gz_x500")
        env_exports.append(f"export PX4_SIM_MODEL='{px4_sim_model}'")

        # Source gz_env.sh to set PX4_GZ_WORLDS and other Gazebo paths
        gz_env_script = self.px4_dir / "build" / "px4_sitl_default" / "rootfs" / "gz_env.sh"
        if gz_env_script.exists():
            env_exports.insert(0, f"source {gz_env_script}")

        # Build full command with environment setup
        env_setup = " && ".join(env_exports) if env_exports else ""
        cmd_str = " ".join([str(arg) for arg in px4_cmd])
        full_cmd = [
            "bash", "-c",
            f"{env_setup} && {cmd_str}" if env_setup else cmd_str
        ]

        # Use blue for Ally, red for Enemy
        color = "blue" if drone_config.name == "Ally" else "red"
        title = f"PX4 {drone_config.name} (Instance {drone_config.instance_id})"

        # Launch from PX4 root directory (PX4 internally changes to rootfs)
        proc = self._launch_in_terminal(
            title=title,
            cmd=full_cmd,
            color=color,
            cwd=str(self.px4_dir)
        )

        if proc:
            self.processes.append((f"px4_{drone_config.name}", proc))
            print(f"[Launcher] ✓ PX4 started for {drone_config.name}")
            time.sleep(3)  # Give PX4 time to initialize
            return True
        else:
            print(f"[Launcher] ERROR: Failed to start PX4 for {drone_config.name}")
            return False

    def launch_enemy_offboard_control(self) -> bool:
        """Launch enemy drone offboard control node in terminal (for multi-drone mode)"""
        print("[Launcher] Starting enemy offboard control...")

        # Use simulator-specific enemy control package
        # Gazebo: gazebo_enemy_control (PX4-based)
        # AirSim: airsim_enemy_control (AirSim API-based)
        simulator_name = self.engine.get_name().lower()
        if simulator_name.startswith("airsim"):
            package_name = "airsim_enemy_control"
        elif simulator_name.startswith("gazebo"):
            package_name = "gazebo_enemy_control"
        else:
            print(f"[Launcher] ERROR: Unknown simulator: {simulator_name}")
            return False

        ws_setup = self.ws_ros2 / "install" / "setup.bash"

        cmd = [
            "bash", "-c",
            f"source /opt/ros/humble/setup.bash && "
            f"source {ws_setup} && "
            f"ros2 run {package_name} enemy_offboard_control"
        ]

        proc = self._launch_in_terminal(
            title=f"Enemy Offboard Control ({simulator_name.capitalize()})",
            cmd=cmd,
            color="red"
        )

        if proc:
            self.processes.append(("enemy_offboard_control", proc))
            print(f"[Launcher] ✓ Enemy offboard control started ({package_name})")
            return True
        else:
            print("[Launcher] ERROR: Failed to start enemy offboard control")
            return False

    def launch_halcon1_pipeline(self, debug: bool, separate_terminals: bool = False,
                                skip_detection: bool = False, skip_tracking: bool = False,
                                skip_guidance: bool = False) -> bool:
        """Launch Halcon1 detection/tracking/guidance pipeline in terminal(s)"""
        print("[Launcher] Starting Halcon1 pipeline...")

        ws_setup = self.ws_ros2 / "install" / "setup.bash"

        if separate_terminals:
            # Launch each node in a separate terminal
            print("[Launcher] Launching nodes in separate terminals...")

            # Common ROS2 parameters
            debug_param = "true" if debug else "false"

            # Detection node (cyan)
            if not skip_detection:
                detection_cmd = [
                    "bash", "-c",
                    f"source /opt/ros/humble/setup.bash && "
                    f"source {ws_setup} && "
                    f"ros2 run detection detection_node --ros-args "
                    f"-p use_sim_time:=false -p debug:={debug_param}"
                ]

                detection_proc = self._launch_in_terminal(
                    title="Halcon1 Detection",
                    cmd=detection_cmd,
                    color="cyan"
                )

                if detection_proc:
                    self.processes.append(("halcon1_detection", detection_proc))
                    print("[Launcher] ✓ Detection node started")
                else:
                    print("[Launcher] ERROR: Failed to start detection node")
                    return False

                time.sleep(1)  # Brief delay between node launches
            else:
                print("[Launcher] ⊗ Skipping detection node")

            # Tracking node (green)
            if not skip_tracking:
                tracking_cmd = [
                    "bash", "-c",
                    f"source /opt/ros/humble/setup.bash && "
                    f"source {ws_setup} && "
                    f"ros2 run tracking tracking_node --ros-args "
                    f"-p use_sim_time:=false -p debug:={debug_param}"
                ]

                tracking_proc = self._launch_in_terminal(
                    title="Halcon1 Tracking",
                    cmd=tracking_cmd,
                    color="green"
                )

                if tracking_proc:
                    self.processes.append(("halcon1_tracking", tracking_proc))
                    print("[Launcher] ✓ Tracking node started")
                else:
                    print("[Launcher] ERROR: Failed to start tracking node")
                    return False

                time.sleep(1)  # Brief delay between node launches
            else:
                print("[Launcher] ⊗ Skipping tracking node")

            # Guidance node (blue)
            if not skip_guidance:
                guidance_cmd = [
                    "bash", "-c",
                    f"source /opt/ros/humble/setup.bash && "
                    f"source {ws_setup} && "
                    f"ros2 run guidance guidance_node --ros-args "
                    f"-p use_sim_time:=false -p debug:={debug_param}"
                ]

                guidance_proc = self._launch_in_terminal(
                    title="Halcon1 Guidance",
                    cmd=guidance_cmd,
                    color="blue"
                )

                if guidance_proc:
                    self.processes.append(("halcon1_guidance", guidance_proc))
                    print("[Launcher] ✓ Guidance node started")
                else:
                    print("[Launcher] ERROR: Failed to start guidance node")
                    return False
            else:
                print("[Launcher] ⊗ Skipping guidance node")

        else:
            # Launch all nodes together using launch file (original behavior)
            print("[Launcher] Launching pipeline with launch file...")

            # Build launch arguments
            launch_args = []
            launch_args.append("debug:=true" if debug else "debug:=false")
            launch_args.append("skip_detection:=true" if skip_detection else "skip_detection:=false")
            launch_args.append("skip_tracking:=true" if skip_tracking else "skip_tracking:=false")
            launch_args.append("skip_guidance:=true" if skip_guidance else "skip_guidance:=false")

            # Print skip warnings
            if skip_detection:
                print("[Launcher] ⊗ Skipping detection node")
            if skip_tracking:
                print("[Launcher] ⊗ Skipping tracking node")
            if skip_guidance:
                print("[Launcher] ⊗ Skipping guidance node")

            launch_args_str = " ".join(launch_args)

            cmd = [
                "bash", "-c",
                f"source /opt/ros/humble/setup.bash && "
                f"source {ws_setup} && "
                f"ros2 launch bringup pipeline.launch.py {launch_args_str}"
            ]

            proc = self._launch_in_terminal(
                title="Halcon1 Pipeline",
                cmd=cmd,
                color="cyan"
            )

            if proc:
                self.processes.append(("halcon1_pipeline", proc))
                print("[Launcher] ✓ Halcon1 pipeline started")
            else:
                print("[Launcher] ERROR: Failed to start Halcon1 pipeline")
                return False

        # Launch RViz2 (always - standard visualization tool)
        print("[Launcher] Launching RViz2...")
        path_to_rviz_config = str(Path(__file__).parent / "rviz_config.rviz") # Same directory where this file is located
        rviz_cmd = [
            "bash", "-c",
            f"source /opt/ros/humble/setup.bash && "
            f"source {ws_setup} && "
            f"ros2 run rviz2 rviz2 -d {path_to_rviz_config}"
        ]

        rviz_proc = self._launch_in_terminal(
            title="RViz2",
            cmd=rviz_cmd,
            color="yellow"
        )

        if rviz_proc:
            self.processes.append(("rviz2", rviz_proc))
            print("[Launcher] ✓ RViz2 started")
        else:
            print("[Launcher] WARNING: Failed to start RViz2")

        return True

    def run(self, args: argparse.Namespace) -> int:
        """Main run loop"""

        # Validate basic environment
        if not self.validate_environment():
            return 1

        # Create drone configuration
        mode = SimulationMode(args.mode)
        drones = self.create_drone_configs(mode)

        # Create configuration (world selection will happen in engine's launch_simulator)
        config = SimulationConfig(
            mode=mode,
            drones=drones,
            debug=args.debug,
            record=False
        )

        # Create the simulation engine
        try:
            self.engine = SimulationEngineFactory.create(args.simulator, config)
            print(f"\n[Launcher] Using {self.engine.get_name()} simulation engine")
        except ValueError as e:
            print(f"[Launcher] ERROR: {e}")
            return 1

        # Validate simulator installation
        is_valid, msg = self.engine.validate_installation()
        if not is_valid:
            print(f"[Launcher] ERROR: {msg}")
            return 1

        print(f"[Launcher] ✓ {msg}")

        # Launch sequence
        print(f"\n[Launcher] {'='*60}")
        print(f"[Launcher] Starting Halcon1 System")
        print(f"[Launcher] Simulator: {self.engine.get_name()}")
        print(f"[Launcher] Mode: {mode.value}")
        print(f"[Launcher] Drones: {len(drones)}")
        print(f"[Launcher] Debug: {args.debug}")
        print(f"[Launcher] {'='*60}\n")

        try:
            # Step 1: Launch simulator
            if not self.engine.launch_simulator():
                print("[Launcher] ERROR: Failed to launch simulator")
                return 1

            # Step 2: Launch MicroXRCE agents
            if not self.launch_microxrce_agents(len(drones)):
                print("[Launcher] ERROR: Failed to launch MicroXRCE agents")
                return 1

            # Step 3: Launch PX4 instances
            # For AirSim: only Ally needs PX4 (Enemy uses SimpleFlight with API)
            # For Gazebo: both drones need PX4
            simulator_name = self.engine.get_name().lower()
            for drone in drones:
                # Skip Enemy PX4 for AirSim (it uses SimpleFlight + AirSim API)
                if simulator_name.startswith("airsim") and drone.name == "Enemy":
                    print(f"[Launcher] Skipping PX4 for {drone.name} (AirSim uses SimpleFlight + API)")
                    continue

                env_vars = self.engine.get_px4_env_vars(drone)
                if not self.launch_px4(drone, env_vars):
                    print(f"[Launcher] ERROR: Failed to launch PX4 for {drone.name}")
                    return 1

            # Step 4: Launch simulator bridges
            if not self.engine.launch_bridges():
                print("[Launcher] ERROR: Failed to launch bridges")
                return 1

            # Step 5: Launch enemy offboard control (only in multi-drone mode)
            if mode == SimulationMode.MULTI_DRONE:
                if not self.launch_enemy_offboard_control():
                    print("[Launcher] ERROR: Failed to launch enemy offboard control")
                    return 1

            # Step 6: Launch Halcon1 pipeline
            if not self.launch_halcon1_pipeline(
                args.debug,
                args.separate_terminals,
                args.skip_detection,
                args.skip_tracking,
                args.skip_guidance
            ):
                print("[Launcher] ERROR: Failed to launch Halcon1 pipeline")
                return 1

            # Step 7: Launch debug visualizers (ally/enemy visualization markers)
            if args.debug:
                if not self.engine.launch_debug_translator(drones):
                    print("[Launcher] WARNING: Failed to launch debug visualizers (non-critical)")

            # Success!
            print(f"\n[Launcher] {'='*60}")
            print(f"[Launcher] ✓ Halcon1 System Running")
            print(f"[Launcher] {'='*60}")
            print(f"[Launcher] Press Ctrl+C to shutdown\n")

            # Wait for Ctrl+C
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n[Launcher] Interrupted by user")

        except Exception as e:
            print(f"[Launcher] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1

        finally:
            self.cleanup()

        return 0

    def cleanup(self):
        """Clean up all processes"""
        print("[Launcher] Cleaning up...")

        # Clean up engine-specific processes
        if self.engine:
            self.engine.cleanup()

        # Clean up our processes
        for name, proc in self.processes:
            try:
                if proc.poll() is None:  # Still running
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"[Launcher] ✓ Stopped {name}")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"[Launcher] ✓ Force killed {name}")
            except Exception as e:
                print(f"[Launcher] WARNING: Error stopping {name}: {e}")

        self.processes.clear()
        print("[Launcher] Cleanup complete")


def main():
    """Entry point"""
    launcher = Halcon1Launcher()
    args = launcher.parse_args()
    return launcher.run(args)


if __name__ == "__main__":
    sys.exit(main())
