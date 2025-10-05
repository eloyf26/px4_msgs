"""
Frame conversion utilities for PX4 ↔ ROS2 coordinate transformations.

Implementation matches PX4's official px4_ros_com/frame_transforms library:
https://github.com/PX4/px4_ros_com/blob/main/include/px4_ros_com/frame_transforms.h
"""

from common_types import DronePose


class CoordinateTransform:
    """Coordinate frame transformations between PX4 and ROS2."""

    @staticmethod
    def ned_to_enu_local_frame(ned_position: list[float]) -> DronePose:
        """
        Transform position from NED (PX4) to ENU (ROS2) frame.

        Args:
            ned_position: Position [x_north, y_east, z_down] in NED frame

        Returns:
            DronePose with position in ENU frame
        """
        return DronePose(
            x=ned_position[1],   # East = NED Y
            y=ned_position[0],   # North = NED X
            z=-ned_position[2]   # Up = -NED Z
        )

    @staticmethod
    def enu_to_ned_local_frame(enu_position: DronePose) -> list[float]:
        """
        Transform position from ENU (ROS2) to NED (PX4) frame.

        Args:
            enu_position: DronePose with position in ENU frame

        Returns:
            Position [x_north, y_east, z_down] in NED frame
        """
        return [
            enu_position.y,   # North = ENU Y
            enu_position.x,   # East = ENU X
            -enu_position.z   # Down = -ENU Z
        ]

    @staticmethod
    def px4_to_ros_orientation(q_px4: list[float]) -> list[float]:
        """
        Transform orientation from PX4 (FRD-to-NED) to ROS2 (FLU-to-ENU).

        Applies both world frame (NED→ENU) and body frame (FRD→FLU) transformations.
        Formula: q_ros = NED_ENU_Q * q_px4 * AIRCRAFT_BASELINK_Q

        Args:
            q_px4: Quaternion [x, y, z, w] representing FRD-to-NED rotation

        Returns:
            Quaternion [x, y, z, w] representing FLU-to-ENU rotation
        """
        import numpy as np
        from scipy.spatial.transform import Rotation as R

        # Static quaternions from PX4's frame_transforms.h
        NED_ENU_Q = R.from_euler('xyz', [np.pi, 0.0, np.pi/2])
        AIRCRAFT_BASELINK_Q = R.from_euler('xyz', [np.pi, 0.0, 0.0])

        r_px4 = R.from_quat(q_px4)
        r_ros = NED_ENU_Q * r_px4 * AIRCRAFT_BASELINK_Q

        return r_ros.as_quat().tolist()

    @staticmethod
    def ros_to_px4_orientation(q_ros: list[float]) -> list[float]:
        """
        Transform orientation from ROS2 (FLU-to-ENU) to PX4 (FRD-to-NED).

        Inverse of px4_to_ros_orientation.
        Formula: q_px4 = NED_ENU_Q * q_ros * AIRCRAFT_BASELINK_Q

        Args:
            q_ros: Quaternion [x, y, z, w] representing FLU-to-ENU rotation

        Returns:
            Quaternion [x, y, z, w] representing FRD-to-NED rotation
        """
        import numpy as np
        from scipy.spatial.transform import Rotation as R

        # Static quaternions (self-inverse for 180° rotations)
        NED_ENU_Q = R.from_euler('xyz', [np.pi, 0.0, np.pi/2])
        AIRCRAFT_BASELINK_Q = R.from_euler('xyz', [np.pi, 0.0, 0.0])

        r_ros = R.from_quat(q_ros)
        r_px4 = NED_ENU_Q * r_ros * AIRCRAFT_BASELINK_Q

        return r_px4.as_quat().tolist()
