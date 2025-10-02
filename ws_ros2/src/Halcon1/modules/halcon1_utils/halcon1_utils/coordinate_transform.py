"""
Frame conversion utilities for PX4 ↔ ROS2 coordinate transformations.

This module provides coordinate frame conversions between:
- NED (North-East-Down): PX4's world/local frame convention
- ENU (East-North-Up): ROS2's standard frame convention (REP-103)

These utilities are reusable across all ROS2 nodes that interface with PX4.
"""

from halcon1_types import DronePose


class CoordinateTransform:
    """Utility class for coordinate frame transformations between PX4 and ROS2."""

    @staticmethod
    def ned_to_enu_position(ned_position: list[float]) -> DronePose:
        """
        Convert position from NED (PX4) to ENU (ROS2) frame.

        NED: X=North, Y=East, Z=Down (PX4 convention)
        ENU: X=East, Y=North, Z=Up (ROS2 convention)

        Transformation: [x_enu, y_enu, z_enu] = [y_ned, x_ned, -z_ned]

        Args:
            ned_position: Position [x_north, y_east, z_down] in NED frame

        Returns:
            DronePose in ENU frame
        """
        return DronePose(
            x=ned_position[1],   # East = y_ned
            y=ned_position[0],   # North = x_ned
            z=-ned_position[2]   # Up = -z_ned
        )

    @staticmethod
    def enu_to_ned_position(enu_position: DronePose) -> list[float]:
        """
        Convert position from ENU (ROS2) to NED (PX4) frame.

        Transformation: [x_ned, y_ned, z_ned] = [y_enu, x_enu, -z_enu]

        Args:
            enu_position: DronePose in ENU frame

        Returns:
            Position [x_north, y_east, z_down] in NED frame
        """
        return [
            enu_position.y,   # North = y_enu
            enu_position.x,   # East = x_enu
            -enu_position.z   # Down = -z_enu
        ]

    @staticmethod
    def ned_to_enu_quaternion(q_ned: list[float]) -> list[float]:
        """
        Convert quaternion from NED (PX4) to ENU (ROS2) frame.

        Args:
            q_ned: Quaternion [x, y, z, w] in NED frame

        Returns:
            Quaternion [x, y, z, w] in ENU frame
        """
        x, y, z, w = q_ned
        return [y, x, -w, -z]

    @staticmethod
    def enu_to_ned_quaternion(q_enu: list[float]) -> list[float]:
        """
        Convert quaternion from ENU (ROS2) to NED (PX4) frame.

        Args:
            q_enu: Quaternion [x, y, z, w] in ENU frame

        Returns:
            Quaternion [x, y, z, w] in NED frame
        """
        x, y, z, w = q_enu
        return [y, x, -w, -z]
