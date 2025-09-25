import numpy as np
from halcon1_types import DronePose
from halcon1_msgs.msg import DroneDetection

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

    def camera_to_world_coordinates(self, drone_detection: DroneDetection, friendly_pose: DronePose) -> DronePose:
        """Convert camera pixel detection to world coordinates"""

        # Mock result --> Drone at constant position, slightly noisy
        x = 28 + np.random.random() * 4
        y = 45 + np.random.random() * 4
        z = 10 + np.random.random() * 2
        return DronePose(x, y, z)