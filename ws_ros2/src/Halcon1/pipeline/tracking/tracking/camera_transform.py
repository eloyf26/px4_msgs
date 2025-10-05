"""
Camera-to-world coordinate transformation utilities for drone tracking.
"""

import numpy as np
from dataclasses import dataclass
from msgs.msg import DroneDetection
from common_types import DronePose
from sensor_msgs.msg import CameraInfo


@dataclass
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    width: float
    height: float


def camera_to_world_coordinates(
    drone_detection: DroneDetection,
    friendly_pose: DronePose,
    friendly_orientation: list[float],
    camera_intrinsics: CameraIntrinsics,
    enemy_drone_width: float,
    enemy_drone_height: float,
    logger=None
) -> DronePose:
    """
    Convert camera pixel detection to world coordinates in ENU frame.

    Args:
        drone_detection: Bounding box detection from camera
        friendly_pose: Friendly drone position in ENU frame
        friendly_orientation: Friendly drone quaternion [x,y,z,w] in ENU frame (FLU-to-ENU)
        camera_intrinsics: Camera intrinsic parameters
        enemy_drone_width: Known width of enemy drone for depth estimation
        enemy_drone_height: Known height of enemy drone for depth estimation
        logger: Optional logger for debug output

    Returns:
        Enemy drone position in ENU frame (ROS2 standard)
    """
    # Get pixel coordinates of the center of the bbox
    u = drone_detection.x + drone_detection.width / 2
    v = drone_detection.y + drone_detection.height / 2

    # Estimate depth from bounding box width and height
    z_width = (enemy_drone_width * camera_intrinsics.fx) / drone_detection.width
    z_height = (enemy_drone_height * camera_intrinsics.fy) / drone_detection.height

    # If estimates differ significantly, log a warning
    if logger and abs(z_width - z_height) / max(z_width, z_height) > 0.5:
        logger.warn(f"Depth estimates from width and height differ significantly: {z_width:.2f} vs {z_height:.2f}")

    depth_meters = (z_width + z_height) / 2  # Average depth estimate

    # Step 1: Pinhole camera projection (produces optical/OpenCV frame convention)
    # Optical frame axes: X=right, Y=down, Z=forward (optical axis)
    offset_right = (u - camera_intrinsics.cx) * depth_meters / camera_intrinsics.fx
    offset_down = (v - camera_intrinsics.cy) * depth_meters / camera_intrinsics.fy
    distance_forward = depth_meters

    # Step 2: Convert optical frame to ROS camera_link frame
    # ROS camera_link frame axes: X=forward, Y=left, Z=up
    camera_frame_x = distance_forward   # forward (was optical Z)
    camera_frame_y = -offset_right      # left = -(right) (was -optical X)
    camera_frame_z = -offset_down       # up = -(down) (was -optical Y)

    # Step 3: Camera frame to body frame
    # Camera frame (ROS): X=forward, Y=left, Z=up
    # Body frame (ROS2 FLU): X=forward, Y=left, Z=up
    # These frames are IDENTICAL, so no transformation needed!
    enemy_position_camera_frame = np.array([camera_frame_x, camera_frame_y, camera_frame_z])
    enemy_position_body_frame = enemy_position_camera_frame  # Identity transform

    # Step 4: Transform from body FLU frame to world ENU frame (dynamic, from quaternion)
    # The quaternion represents FLU-to-ENU rotation (converted from PX4's FRD-to-NED)
    # Rotation matrix R transforms body vectors to world: v_world_enu = R @ v_body_flu
    rotation_matrix = quaternion_to_rotation_matrix(friendly_orientation)
    enemy_position_world_relative = rotation_matrix @ enemy_position_body_frame

    # Debug logging
    if logger:
        logger.info(f'Camera frame: [{camera_frame_x:.2f}, {camera_frame_y:.2f}, {camera_frame_z:.2f}]')
        logger.info(f'Body frame: [{enemy_position_body_frame[0]:.2f}, {enemy_position_body_frame[1]:.2f}, {enemy_position_body_frame[2]:.2f}]')
        logger.info(f'Friendly quaternion (ENU): {friendly_orientation}')
        logger.info(f'After rotation: [{enemy_position_world_relative[0]:.2f}, {enemy_position_world_relative[1]:.2f}, {enemy_position_world_relative[2]:.2f}]')

    rotated_position = enemy_position_world_relative

    # Step 5: Add friendly drone's absolute position to get enemy's absolute position
    camera_position = np.array([friendly_pose.x, friendly_pose.y, friendly_pose.z])

    if logger:
        logger.info(f'After rotation: [{rotated_position[0]:.2f}, {rotated_position[1]:.2f}, {rotated_position[2]:.2f}]')

    enemy_position_world = camera_position + rotated_position

    if logger:
        logger.info(f'Final world position: [{enemy_position_world[0]:.2f}, {enemy_position_world[1]:.2f}, {enemy_position_world[2]:.2f}]')

    return DronePose(enemy_position_world[0], enemy_position_world[1], enemy_position_world[2])


def quaternion_to_rotation_matrix(q: list[float]) -> np.ndarray:
    """Convert quaternion [x, y, z, w] to rotation matrix"""
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


def parse_camera_intrinsics(camera_info: CameraInfo, logger=None) -> CameraIntrinsics:
    """Extract camera intrinsic parameters from CameraInfo message"""
    # Check that there is no distortion
    if camera_info.distortion_model != 'plumb_bob':
        if logger:
            logger.error(f'Unsupported distortion model: {camera_info.distortion_model}')
        return None

    k = camera_info.k  # length-9 list
    if len(k) != 9:
        if logger:
            logger.error('Invalid camera intrinsic matrix size')
        return None

    return CameraIntrinsics(
        fx=k[0],
        fy=k[4],
        cx=k[2],
        cy=k[5],
        width=camera_info.width,
        height=camera_info.height
    )
