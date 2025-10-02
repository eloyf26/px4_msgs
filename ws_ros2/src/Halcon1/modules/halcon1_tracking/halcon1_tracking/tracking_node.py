import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from halcon1_msgs.msg import DroneDetection
from geometry_msgs.msg import PoseStamped
from px4_msgs.msg import VehicleOdometry
from halcon1_utils import CoordinateTransform
from halcon1_types import DronePose
from sensor_msgs.msg import CameraInfo
from dataclasses import dataclass
import numpy as np

@dataclass
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    width: float
    height: float

class TrackingNode(Node):
    def __init__(self):
        super().__init__('tracking_node')

        # QoS profile for PX4 topics
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Publishers
        self.enemy_pose_pub = self.create_publisher(PoseStamped, '/enemy/pose', 10)

        # Subscribers
        self.detection_sub = self.create_subscription(
            DroneDetection, '/enemy/detection',
            self.detection_callback, 10)
        self.friendly_sub = self.create_subscription(
            VehicleOdometry, '/fmu/out/vehicle_odometry',
            self.friendly_callback, qos_profile)
        self.camera_info_sub = self.create_subscription(
            CameraInfo, '/camera/camera_info',
            self.camera_info_callback, 10)

        # Camera intrinsics
        self.camera_intrinsics = None
        self.last_intrinsic_update = None

        # Enemy drone dimensions for depth estimation
        # TODO: Should be ros2 parameters
        self.enemy_drone_width = 0.5
        self.enemy_drone_height = 0.2

        # State
        self.friendly_pose = None
        self.friendly_orientation = None

        self.get_logger().info('Tracking node initialized - waiting for detections and friendly pose...')

    def friendly_callback(self, msg):
        """Update friendly drone pose from PX4 odometry (includes orientation)"""
        # Convert position from NED to ENU
        self.friendly_pose = CoordinateTransform.ned_to_enu_position(msg.position)

        # Convert orientation quaternion from NED to ENU
        self.friendly_orientation = CoordinateTransform.ned_to_enu_quaternion(list(msg.q))

    def camera_info_callback(self, msg):
        """Update the camera intrinsic parameters from CameraInfo message"""
        # We don't want to update intrinsics every time because they should be constant. We will only do it every 5 seconds
        if self.last_intrinsic_update is not None:
            if (self.get_clock().now() - self.last_intrinsic_update).nanoseconds < 5e9:
                return  # 5 seconds
        self.last_intrinsic_update = self.get_clock().now()

        self.camera_intrinsics = self._parse_camera_intrinsics(msg)

    def detection_callback(self, msg):
        """Process enemy detection and transform to world coordinates"""
        # Need friendly pose and orientation for coordinate transformation
        if self.friendly_pose is None:
            self.get_logger().info('No friendly pose/orientation available, skipping detection processing')
            return

        if self.last_intrinsic_update is None:
            self.get_logger().info('No camera intrinsics available, skipping detection processing')
            return

        # Log detection values for debugging
        self.get_logger().info(f'Detection received: x={msg.x}, y={msg.y}, width={msg.width}, height={msg.height}')

        # Validate detection data
        if msg.width <= 0 or msg.height <= 0:
            self.get_logger().error(f'Invalid detection dimensions: width={msg.width}, height={msg.height}. '
                                   f'Full detection: x={msg.x}, y={msg.y}, width={msg.width}, height={msg.height}')
            self.get_logger().error('Skipping coordinate transformation due to invalid detection')
            return

        enemy_world_pose = self._camera_to_world_coordinates(msg, self.friendly_pose, self.friendly_orientation)

        if not enemy_world_pose:
            self.get_logger().error('Coordinate transformation failed, skipping publishing')
            return

        # Create and publish PoseStamped message
        pose_msg = PoseStamped()
        pose_msg.header.stamp = msg.header.stamp  # Propagate original detection timestamp
        pose_msg.header.frame_id = 'world'

        # Position from coordinate transform result
        pose_msg.pose.position.x = enemy_world_pose.x
        pose_msg.pose.position.y = enemy_world_pose.y
        pose_msg.pose.position.z = enemy_world_pose.z

        # Orientation (identity quaternion for now as requested)
        pose_msg.pose.orientation.x = 0.0
        pose_msg.pose.orientation.y = 0.0
        pose_msg.pose.orientation.z = 0.0
        pose_msg.pose.orientation.w = 1.0

        self.enemy_pose_pub.publish(pose_msg)

    def _camera_to_world_coordinates(self, drone_detection: DroneDetection,
                                     friendly_pose: DronePose, friendly_orientation) -> DronePose:
        """
        Convert camera pixel detection to world coordinates in ENU frame.

        Args:
            drone_detection: Bounding box detection from camera
            friendly_pose: Friendly drone position in ENU frame
            friendly_orientation: Friendly drone quaternion in ENU frame

        Returns:
            Enemy drone position in ENU frame (ROS2 standard)
        """
        # Get pixel coordinates of the center of the bbox
        u = drone_detection.x + drone_detection.width / 2
        v = drone_detection.y + drone_detection.height / 2

        # Estimate depth from bounding box width and height
        z_width = (self.enemy_drone_width * self.camera_intrinsics.fx) / drone_detection.width
        z_height = (self.enemy_drone_height * self.camera_intrinsics.fy) / drone_detection.height

        # If estimates differ significantly, log a warning
        if abs(z_width - z_height) / max(z_width, z_height) > 0.5:
            self.get_logger().warn(f"Depth estimates from width and height differ significantly: {z_width:.2f} vs {z_height:.2f}")

        depth_meters = (z_width + z_height) / 2  # Average depth estimate

        # Step 1: Pinhole camera projection (produces optical/OpenCV frame convention)
        # Optical frame axes: X=right, Y=down, Z=forward (optical axis)
        offset_right = (u - self.camera_intrinsics.cx) * depth_meters / self.camera_intrinsics.fx
        offset_down = (v - self.camera_intrinsics.cy) * depth_meters / self.camera_intrinsics.fy
        distance_forward = depth_meters

        # Step 2: Convert optical frame to ROS camera_link frame
        # ROS camera_link frame axes: X=forward, Y=left, Z=up
        camera_frame_x = distance_forward   # forward (was optical Z)
        camera_frame_y = -offset_right      # left = -(right) (was -optical X)
        camera_frame_z = -offset_down       # up = -(down) (was -optical Y)

        # Step 3: Transform camera frame to world frame using friendly drone orientation
        rotation_matrix = self._quaternion_to_rotation_matrix(friendly_orientation)
        enemy_position_camera_frame = np.array([camera_frame_x, camera_frame_y, camera_frame_z])

        # TEMPORARY FIX: Hardcoded rotation for camera pointing North (+Y in ENU)
        # Camera frame: X=forward, Y=left, Z=up
        # World frame (ENU): X=East, Y=North, Z=Up
        # Mapping: Camera +X (forward) → World +Y (North)
        #          Camera +Y (left) → World -X (West)
        #          Camera +Z (up) → World +Z (Up)
        rotation_matrix_fixed = np.array([
            [ 0, -1,  0],  # World X = -Camera Y (left→West means -left→East)
            [ 1,  0,  0],  # World Y = Camera X (forward→North)
            [ 0,  0,  1]   # World Z = Camera Z (up→up)
        ])

        # Debug logging
        self.get_logger().info(f'Camera frame position: [{camera_frame_x:.2f}, {camera_frame_y:.2f}, {camera_frame_z:.2f}]')
        self.get_logger().info(f'Friendly quaternion: {friendly_orientation}')
        self.get_logger().info(f'Rotation matrix (from quat):\n{rotation_matrix}')
        self.get_logger().info(f'Rotation matrix (fixed):\n{rotation_matrix_fixed}')

        # Use fixed matrix for now
        rotation_matrix = rotation_matrix_fixed

        # Step 4: Add friendly drone's absolute position to get enemy's absolute position
        camera_position = np.array([friendly_pose.x, friendly_pose.y, friendly_pose.z])
        rotated_position = rotation_matrix @ enemy_position_camera_frame
        self.get_logger().info(f'After rotation: [{rotated_position[0]:.2f}, {rotated_position[1]:.2f}, {rotated_position[2]:.2f}]')

        enemy_position_world = camera_position + rotated_position
        self.get_logger().info(f'Final world position: [{enemy_position_world[0]:.2f}, {enemy_position_world[1]:.2f}, {enemy_position_world[2]:.2f}]')

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

    def _parse_camera_intrinsics(self, camera_info) -> CameraIntrinsics:
        """Extract camera intrinsic parameters from CameraInfo message"""
        # Check that there is no distortion
        if camera_info.distortion_model != 'plumb_bob':
            self.get_logger().error(f'Unsupported distortion model: {camera_info.distortion_model}')
            return None

        k = camera_info.k  # length-9 list
        if len(k) != 9:
            self.get_logger().error('Invalid camera intrinsic matrix size')
            return None

        return CameraIntrinsics(
            fx=k[0],
            fy=k[4],
            cx=k[2],
            cy=k[5],
            width=camera_info.width,
            height=camera_info.height
        )

def main():
    rclpy.init()
    node = TrackingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()