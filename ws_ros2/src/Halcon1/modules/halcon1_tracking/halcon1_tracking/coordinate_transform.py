import numpy as np

class CoordinateTransform:
    def __init__(self):
        # Camera intrinsic parameters
        self.fx = 500.0  # focal length x (pixels)
        self.fy = 500.0  # focal length y (pixels)
        self.cx = 320.0  # principal point x (pixels)
        self.cy = 240.0  # principal point y (pixels)

        # Camera mounting (forward-facing, aligned with body frame)
        # Assuming camera frame = body frame for simplicity
        self.camera_to_body = np.eye(3)

    def pixel_to_bearing_vector(self, pixel_x, pixel_y):
        """Convert pixel coordinates to unit bearing vector in camera frame"""
        # Normalize pixel coordinates
        x_norm = (pixel_x - self.cx) / self.fx
        y_norm = (pixel_y - self.cy) / self.fy

        # Bearing vector in camera frame (forward is +Z in camera)
        bearing_camera = np.array([x_norm, y_norm, 1.0])
        bearing_camera = bearing_camera / np.linalg.norm(bearing_camera)

        return bearing_camera

    def quaternion_to_rotation_matrix(self, q):
        """Convert quaternion [w, x, y, z] to rotation matrix"""
        w, x, y, z = q
        R = np.array([
            [1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
            [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
            [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]
        ])
        return R

    def pixel_to_world_ned(self, pixel_x, pixel_y, friendly_pos_ned,
                          friendly_quaternion=None, estimated_distance=10.0):
        """
        Transform pixel detection to world NED coordinates

        Args:
            pixel_x, pixel_y: Detection in image pixels
            friendly_pos_ned: [x, y, z] position of friendly drone in NED
            friendly_quaternion: [w, x, y, z] orientation (optional)
            estimated_distance: Assumed distance to target (meters)

        Returns:
            enemy_pos_ned: [x, y, z] estimated position in world NED frame
        """
        # Get bearing vector in camera frame
        bearing_camera = self.pixel_to_bearing_vector(pixel_x, pixel_y)

        # Transform to body frame (assuming camera aligned with body)
        bearing_body = self.camera_to_body @ bearing_camera

        # Transform to NED frame
        if friendly_quaternion is not None:
            R_body_to_ned = self.quaternion_to_rotation_matrix(friendly_quaternion)
            bearing_ned = R_body_to_ned @ bearing_body
        else:
            # Assume drone is level and pointing north
            bearing_ned = bearing_body

        # Scale by estimated distance
        relative_pos_ned = bearing_ned * estimated_distance

        # Add friendly position to get world position
        enemy_pos_ned = friendly_pos_ned + relative_pos_ned

        return enemy_pos_ned