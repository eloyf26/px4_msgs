import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from halcon1_msgs.msg import DroneDetection
from geometry_msgs.msg import PoseStamped
from px4_msgs.msg import VehicleOdometry
from halcon1_tracking.coordinate_transform import CoordinateTransform
from halcon1_types import DronePose

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

        # Coordinate transform
        self.transform = CoordinateTransform()

        # State
        self.friendly_pose = None
        self.friendly_orientation = None

        self.get_logger().info('Tracking node initialized - waiting for detections and friendly pose...')

    def friendly_callback(self, msg):
        """Update friendly drone pose from PX4 odometry (includes orientation)"""
        # Store position
        self.friendly_pose = DronePose(
            x=msg.position[0],
            y=msg.position[1],
            z=msg.position[2]
        )
        # Store orientation quaternion
        self.friendly_orientation = msg.q

    def detection_callback(self, msg):
        """Process enemy detection and transform to world coordinates"""
        # Need friendly pose and orientation for coordinate transformation
        if self.friendly_pose is None or self.friendly_orientation is None:
            self.get_logger().info('No friendly pose/orientation available for coordinate transformation')
            return

        # Log detection values for debugging
        self.get_logger().info(f'Detection received: x={msg.x}, y={msg.y}, width={msg.width}, height={msg.height}')

        # Validate detection data
        if msg.width <= 0 or msg.height <= 0:
            self.get_logger().error(f'Invalid detection dimensions: width={msg.width}, height={msg.height}. '
                                   f'Full detection: x={msg.x}, y={msg.y}, width={msg.width}, height={msg.height}')
            self.get_logger().error('Skipping coordinate transformation due to invalid detection')
            return

        try:
            # Use the coordinate transform to convert to world coordinates
            enemy_world_pose = self.transform.camera_to_world_coordinates(
                msg, self.friendly_pose, self.friendly_orientation)
        except ValueError as e:
            self.get_logger().error(f'Coordinate transformation failed: {e}')
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

def main():
    rclpy.init()
    node = TrackingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()