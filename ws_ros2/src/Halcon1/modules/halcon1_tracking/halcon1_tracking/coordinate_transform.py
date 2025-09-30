import numpy as np
import yaml
from pathlib import Path
from halcon1_types import DronePose
from halcon1_msgs.msg import DroneDetection

from dataclasses import dataclass

@dataclass
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    width: float
    height: float

class CoordinateTransform:
    def __init__(self, enemy_drone_width: float = 0.5, enemy_drone_height: float = 0.2):
        self.camera_intrinsics = None
        self.enemy_drone_width = enemy_drone_width
        self.enemy_drone_height = enemy_drone_height

    def update_camera_intrinsics(self, intrinsics: CameraIntrinsics):
        self.camera_intrinsics = intrinsics

    def camera_to_world_coordinates(self, drone_detection: DroneDetection,
                                  friendly_pose: DronePose, friendly_orientation) -> DronePose:
        """
        Convert camera pixel detection to world coordinates
        Safe to assume camera_intrinsics, friendly_pose, and friendly_orientation are set
        """
        # Get pixel coordinates of the center of the bbox
        u = drone_detection.x + drone_detection.width / 2
        v = drone_detection.y + drone_detection.height / 2

        # Estimate depth from bounding box width and height
        z_width = (self.enemy_drone_width * self.camera_intrinsics.fx) / drone_detection.width
        z_height = (self.enemy_drone_height * self.camera_intrinsics.fy) / drone_detection.height
        # If estimates differ significantly, log a warning
        if abs(z_width - z_height) / max(z_width, z_height) > 0.5:
            print(f"Warning: Depth estimates from width and height differ significantly: {z_width:.2f} vs {z_height:.2f}")

        z = (z_width + z_height) / 2  # Average depth estimate

        # Convert u, v coordinates to ray in the camera frame
        x_camera = (u - self.camera_intrinsics.cx) * z / self.camera_intrinsics.fx
        y_camera = (v - self.camera_intrinsics.cy) * z / self.camera_intrinsics.fy
        z_camera = z

        # Transform camera frame coordinates to world frame coordinates using the friendly pose and orientation
        rotation_matrix = CoordinateTransform._quaternion_to_rotation_matrix(friendly_orientation)
        enemy_position_camera_frame = np.array([x_camera, y_camera, z_camera])
        camera_position = np.array([friendly_pose.x, friendly_pose.y, friendly_pose.z])
        enemy_position_world = camera_position + rotation_matrix @ enemy_position_camera_frame

        return DronePose(enemy_position_world[0], enemy_position_world[1], enemy_position_world[2])

    @staticmethod
    def _quaternion_to_rotation_matrix(q: list[float]):
        """Convert quaternion (x, y, z, w) to rotation matrix"""
        x, y, z, w = q
        # normalize (safety)
        n = x*x + y*y + z*z + w*w
        if n < 1e-12:
            return np.eye(3)
        s = 2.0 / n

        xx = x * x * s
        yy = y * y * s
        zz = z * z * s
        xy = x * y * s
        xz = x * z * s
        yz = y * z * s
        wx = w * x * s
        wy = w * y * s
        wz = w * z * s

        return np.array([
            [1.0 - (yy + zz),      xy - wz,          xz + wy],
            [     xy + wz,     1.0 - (xx + zz),      yz - wx],
            [     xz - wy,         yz + wx,      1.0 - (xx + yy)]
        ])
