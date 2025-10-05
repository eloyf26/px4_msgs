#!/usr/bin/env python3
"""
Simulation Engine Interface
Abstract base class for simulation engines (Gazebo, AirSim, Isaac Sim, etc.)

This interface defines the contract that all simulation engines must implement.
It enables seamless switching between different simulators while keeping the
Halcon1 core logic (detection, tracking, guidance) completely unchanged.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SimulationMode(Enum):
    """Simulation modes supported by the system"""
    SINGLE_DRONE = "single"      # Single ally drone
    MULTI_DRONE = "multi"        # Ally + Enemy drones
    HARDWARE = "hardware"        # Real hardware (no simulation)


@dataclass
class DroneConfig:
    """Configuration for a single drone"""
    name: str                    # Drone identifier (e.g., "Ally", "Enemy")
    instance_id: int            # PX4 instance ID (0, 1, 2, ...)
    position: Tuple[float, float, float]  # Initial position (x, y, z)
    yaw: float = 0.0            # Initial yaw in degrees
    has_camera: bool = True     # Whether drone has a camera
    camera_config: Optional[Dict] = None  # Camera configuration


@dataclass
class SimulationConfig:
    """Overall simulation configuration"""
    mode: SimulationMode
    drones: List[DroneConfig]
    debug: bool = False         # Enable debug visualizations (RViz2)
    record: bool = False        # Record simulation data


class SimulationEngine(ABC):
    """
    Abstract base class for simulation engines.

    Each simulation engine (Gazebo, AirSim, Isaac) must implement this interface
    to integrate with the Halcon1 system.
    """

    def __init__(self, config: SimulationConfig):
        """
        Initialize the simulation engine with configuration.

        Args:
            config: Simulation configuration including drones, mode, etc.
        """
        self.config = config
        self.processes = []  # Track launched processes for cleanup

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this simulation engine (e.g., 'Gazebo', 'AirSim')"""
        pass

    @abstractmethod
    def validate_installation(self) -> Tuple[bool, str]:
        """
        Check if the simulation engine is properly installed.

        Returns:
            (is_valid, message): Boolean indicating if valid, and a message
        """
        pass

    @abstractmethod
    def get_camera_topic(self, drone_name: str = "Ally") -> str:
        """
        Get the ROS2 topic name for camera images.

        Args:
            drone_name: Name of the drone (for multi-drone setups)

        Returns:
            ROS2 topic name (e.g., "/camera/image")
        """
        pass

    @abstractmethod
    def get_px4_connection_config(self, instance_id: int) -> Dict:
        """
        Get PX4 connection configuration for this simulator.

        Args:
            instance_id: PX4 instance ID (0 for first drone, 1 for second, etc.)

        Returns:
            Dictionary with keys like:
            - protocol: "tcp" or "udp"
            - port: Port number for MAVLink
            - address: IP address (usually "localhost")
        """
        pass

    @abstractmethod
    def launch_simulator(self) -> bool:
        """
        Launch the simulator (environment/physics engine).

        This should start the 3D environment and prepare for PX4 connections.

        Returns:
            True if launched successfully, False otherwise
        """
        pass

    @abstractmethod
    def launch_bridges(self) -> bool:
        """
        Launch ROS2 bridges (camera bridge, visualization translators, etc.).

        These bridges convert simulator-specific topics to standard ROS2 topics
        that Halcon1 nodes expect (e.g., /camera/image, /camera/camera_info).

        Returns:
            True if launched successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_px4_env_vars(self, drone_config: DroneConfig) -> Dict[str, str]:
        """
        Get environment variables needed for PX4 SITL.

        Args:
            drone_config: Configuration for this specific drone

        Returns:
            Dictionary of environment variable names and values
        """
        pass

    @abstractmethod
    def launch_debug_translator(self, drones: List['DroneConfig']) -> bool:
        """
        Launch debug visualization translator for RViz.

        Different simulators handle debug visualization differently:
        - Gazebo: Adds offset to enemy PX4 position (both drones report local (0,0,0))
        - AirSim: Subtracts offset from AirSim API position (queries global position)

        Args:
            drones: List of drone configurations with spawn positions

        Returns:
            True if launched successfully, False otherwise
        """
        pass

    @abstractmethod
    def cleanup(self) -> bool:
        """
        Clean up all simulator processes.

        This should kill simulator, bridges, and any other spawned processes.

        Returns:
            True if cleanup successful, False otherwise
        """
        pass

    @abstractmethod
    def get_default_world(self) -> str:
        """
        Get the default world/environment name for this simulator.

        This allows each simulator to define its own sensible default.

        Returns:
            Default world name (e.g., "default" for Gazebo, "blocks" for AirSim)
        """
        pass

    @abstractmethod
    def get_available_worlds(self) -> List[str]:
        """
        Get list of available/supported worlds for this simulator.

        Returns:
            List of world names that can be passed to --world parameter
        """
        pass

    @abstractmethod
    def validate_world(self, world_name: str) -> Tuple[bool, str]:
        """
        Validate if a world is available and can be used.

        Args:
            world_name: Name of world to validate

        Returns:
            (is_valid, message): Boolean and descriptive message
        """
        pass

    @abstractmethod
    def get_world_launch_info(self, world_name: str) -> Dict[str, str]:
        """
        Get information needed to launch a specific world.

        Args:
            world_name: Name of world to launch

        Returns:
            Dictionary with simulator-specific launch info
            (paths, scripts, environment variables, etc.)
        """
        pass

    def get_microxrce_port(self, instance_id: int) -> int:
        """
        Get MicroXRCE-DDS agent port for a PX4 instance.

        Default implementation: 8888 + instance_id
        Override if your simulator needs different ports.

        Args:
            instance_id: PX4 instance ID

        Returns:
            UDP port number for MicroXRCE-DDS agent
        """
        return 8888 + instance_id

    def get_required_packages(self) -> List[str]:
        """
        Get list of ROS2 packages required for this simulator.

        Default implementation returns empty list.
        Override to specify simulator-specific packages.

        Returns:
            List of ROS2 package names
        """
        return []

    def get_documentation_url(self) -> Optional[str]:
        """
        Get URL or path to simulator-specific documentation.

        Returns:
            URL or file path to documentation, or None
        """
        return None

    def supports_feature(self, feature: str) -> bool:
        """
        Check if this simulator supports a specific feature.

        Args:
            feature: Feature name (e.g., "depth_camera", "lidar", "gpu_acceleration")

        Returns:
            True if feature is supported, False otherwise
        """
        # Default: no special features
        # Override to specify supported features
        return False


class SimulationEngineFactory:
    """Factory class to create simulation engines"""

    _engines = {}

    @classmethod
    def register_engine(cls, name: str, engine_class: type):
        """
        Register a simulation engine class.

        Args:
            name: Engine name (e.g., "gazebo", "airsim", "isaac")
            engine_class: Class that implements SimulationEngine
        """
        cls._engines[name.lower()] = engine_class

    @classmethod
    def create(cls, name: str, config: SimulationConfig) -> SimulationEngine:
        """
        Create a simulation engine instance.

        Args:
            name: Engine name (e.g., "gazebo", "airsim")
            config: Simulation configuration

        Returns:
            Instance of the requested simulation engine

        Raises:
            ValueError: If engine name is not registered
        """
        name_lower = name.lower()
        if name_lower not in cls._engines:
            available = ', '.join(cls._engines.keys())
            raise ValueError(
                f"Unknown simulation engine '{name}'. "
                f"Available engines: {available}"
            )

        engine_class = cls._engines[name_lower]
        return engine_class(config)

    @classmethod
    def list_engines(cls) -> List[str]:
        """
        Get list of registered engine names.

        Returns:
            List of engine names
        """
        return list(cls._engines.keys())
