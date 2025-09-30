import numpy as np
import yaml
from pathlib import Path
from halcon1_types import DronePose
from halcon1_msgs.msg import DroneDetection

class CoordinateTransform:
    def __init__(self):
        # Load configuration from YAML file
        self._load_config()

        print(f"Coordinate transform initialized with camera at ({self.camera_offset[0]:.2f}, {self.camera_offset[1]:.2f}, {self.camera_offset[2]:.2f})m")

    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            import halcon1_tracking
            package_dir = Path(halcon1_tracking.__file__).parent
            config_path = package_dir / 'config.yaml'
        except ImportError:
            # Fallback if package not properly installed
            config_path = Path(__file__).parent / 'config.yaml'

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Camera intrinsic parameters
        self.fx = config['camera_intrinsics']['fx']
        self.fy = config['camera_intrinsics']['fy']
        self.cx = config['camera_intrinsics']['cx']
        self.cy = config['camera_intrinsics']['cy']

        # Camera mounting position relative to drone base
        mount = config['camera_mount']
        self.camera_offset = np.array([mount['x'], mount['y'], mount['z']])

        # Enemy drone width for depth estimation
        self.drone_physical_width = config['drone']['enemy_width']

    def quaternion_to_rotation_matrix(self, q):
        """Convert quaternion to 3x3 rotation matrix"""
        # q = [x, y, z, w] in px4_msgs format
        x, y, z, w = q[0], q[1], q[2], q[3]

        R = np.array([
            [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]
        ])
        return R

    def camera_to_world_coordinates(self, drone_detection: DroneDetection,
                                  friendly_pose: DronePose, friendly_orientation) -> DronePose:
        """Convert camera pixel detection to world coordinates"""

        # Validate input data
        if drone_detection.width <= 0:
            raise ValueError(f"Invalid detection width: {drone_detection.width}. "
                           f"Detection: x={drone_detection.x}, y={drone_detection.y}, "
                           f"width={drone_detection.width}, height={drone_detection.height}")

        # Step 1: Convert pixel to normalized camera coordinates
        u_normalized = (drone_detection.x - self.cx) / self.fx
        v_normalized = (drone_detection.y - self.cy) / self.fy

        # Step 2: Estimate depth from bounding box width
        # depth = (known_width * focal_length) / bbox_width_pixels
        depth = (self.drone_physical_width * self.fx) / drone_detection.width

        # Step 3: Get 3D point in camera frame
        point_camera = np.array([
            u_normalized * depth,
            v_normalized * depth,
            depth
        ])

        # Step 4: Transform to body frame (add camera offset)
        point_body = point_camera + self.camera_offset

        # Step 5: Apply drone rotation (body to world)
        R = self.quaternion_to_rotation_matrix(friendly_orientation)
        point_world = R @ point_body

        # Step 6: Add drone position to get world coordinates
        enemy_x = point_world[0] + friendly_pose.x
        enemy_y = point_world[1] + friendly_pose.y
        enemy_z = point_world[2] + friendly_pose.z

        return DronePose(enemy_x, enemy_y, enemy_z)