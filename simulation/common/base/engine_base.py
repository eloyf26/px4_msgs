#!/usr/bin/env python3
"""
Base class for simulation engines with common functionality.

This class extracts all the boilerplate code that was duplicated across
Gazebo and AirSim engines, making it much easier to add new simulators.

New simulation engines should inherit from this class instead of SimulationEngine directly.
"""

import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "interfaces"))
from sim_engine import SimulationEngine, SimulationConfig


class SimulationEngineBase(SimulationEngine):
    """
    Base class providing common functionality for all simulation engines.

    Provides:
    - Terminal detection and process launching
    - Common path setup (repo_root, px4_dir, ws_ros2)
    - Generic process cleanup
    - Default implementations for optional interface methods

    New engines only need to implement simulator-specific logic.
    """

    def __init__(self, config: SimulationConfig):
        """
        Initialize base simulation engine.

        Sets up common paths and process tracking.
        """
        super().__init__(config)

        # Common paths (used by all engines)
        self.repo_root = Path(__file__).parent.parent.parent.parent
        self.px4_dir = self.repo_root / "external" / "PX4-Autopilot"
        self.ws_ros2 = self.repo_root / "ws_ros2"

        # Process tracking for cleanup
        self.processes = []

    # =================================================================
    # TERMINAL UTILITIES (extracted from duplicated code)
    # =================================================================

    def _detect_terminal(self) -> tuple:
        """
        Detect available terminal emulator.

        Returns:
            (command, supports_title): Tuple of terminal command and whether it supports --title
        """
        if shutil.which("gnome-terminal"):
            return ("gnome-terminal", True)
        elif shutil.which("xterm"):
            return ("xterm", True)
        elif shutil.which("konsole"):
            return ("konsole", True)
        elif shutil.which("terminator"):
            return ("terminator", True)
        else:
            print(f"[{self.get_name()}] WARNING: No terminal emulator found. Processes will run hidden.")
            print(f"[{self.get_name()}]          Install gnome-terminal: sudo apt install gnome-terminal")
            return (None, False)

    def _launch_in_terminal(
        self,
        title: str,
        cmd: list,
        color: str = "green",
        cwd: Optional[str] = None
    ) -> Optional[subprocess.Popen]:
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
            print(f"[{self.get_name()}] WARNING: Launching '{title}' without terminal")
            try:
                proc = subprocess.Popen(cmd, cwd=cwd)
                return proc
            except Exception as e:
                print(f"[{self.get_name()}] ERROR: Failed to launch {title}: {e}")
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
            print(f"[{self.get_name()}] ERROR: Failed to launch terminal for {title}: {e}")
            return None

    # =================================================================
    # PROCESS MANAGEMENT (common cleanup logic)
    # =================================================================

    def _cleanup_processes(self) -> bool:
        """
        Clean up tracked processes.

        This is the common cleanup logic. Engines can override cleanup()
        to add simulator-specific cleanup, then call this method.

        Returns:
            True if all processes cleaned up successfully
        """
        success = True

        for name, proc in self.processes:
            try:
                if proc.poll() is None:  # Still running
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"[{self.get_name()}] ✓ Stopped {name}")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"[{self.get_name()}] ✓ Force killed {name}")
            except Exception as e:
                print(f"[{self.get_name()}] WARNING: Error stopping {name}: {e}")
                success = False

        self.processes.clear()
        return success

    def cleanup(self) -> bool:
        """
        Default cleanup implementation.

        Engines can override this to add custom cleanup,
        but should call super().cleanup() to clean tracked processes.
        """
        print(f"[{self.get_name()}] Cleaning up...")
        return self._cleanup_processes()

    # =================================================================
    # DEFAULT IMPLEMENTATIONS (optional interface methods)
    # =================================================================

    def get_microxrce_port(self, instance_id: int) -> int:
        """
        Get MicroXRCE-DDS agent port for a PX4 instance.

        Default implementation: 8888 + instance_id
        Override if your simulator needs different ports.
        """
        return 8888 + instance_id

    def get_required_packages(self) -> List[str]:
        """
        Get list of ROS2 packages required for this simulator.

        Default implementation returns empty list.
        Override to specify simulator-specific packages.
        """
        return []

    def get_documentation_url(self) -> Optional[str]:
        """
        Get URL or path to simulator-specific documentation.

        Default implementation returns None.
        Override to specify docs path.
        """
        return None

    def supports_feature(self, feature: str) -> bool:
        """
        Check if this simulator supports a specific feature.

        Default implementation returns False for all features.
        Override to specify supported features.

        Args:
            feature: Feature name (e.g., "depth_camera", "lidar", "gpu_acceleration")
        """
        return False

    def get_default_world(self) -> str:
        """
        Get the default world/environment name for this simulator.

        Default implementation returns "default".
        Override if your simulator has a different default.
        """
        return "default"

    def get_available_worlds(self) -> List[str]:
        """
        Get list of available/supported worlds for this simulator.

        Default implementation returns ["default"].
        Override to list your simulator's worlds.
        """
        return ["default"]

    def validate_world(self, world_name: str) -> Tuple[bool, str]:
        """
        Validate if a world is available and can be used.

        Default implementation checks if world_name is in get_available_worlds().
        Override for custom validation logic.

        Args:
            world_name: Name of world to validate

        Returns:
            (is_valid, message): Boolean and descriptive message
        """
        available = self.get_available_worlds()
        if world_name not in available:
            return False, (
                f"Unknown world '{world_name}'. "
                f"Available: {', '.join(available)}"
            )
        return True, f"World '{world_name}' is available"

    def get_world_launch_info(self, world_name: str) -> dict:
        """
        Get information needed to launch a specific world.

        Default implementation returns basic info.
        Override for simulator-specific launch details.

        Args:
            world_name: Name of world to launch

        Returns:
            Dictionary with launch info
        """
        return {
            "type": self.get_name().lower(),
            "world_name": world_name,
            "requires_manual_launch": False
        }
