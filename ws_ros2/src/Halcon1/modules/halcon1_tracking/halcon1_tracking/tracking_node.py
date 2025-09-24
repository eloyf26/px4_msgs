import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from halcon1_msgs.msg import DroneDetection
from geometry_msgs.msg import PoseStamped
from px4_msgs.msg import VehicleLocalPosition, VehicleOdometry
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

        self.get_logger().info('Tracking node initialized - waiting for detections and friendly pose...')

    def friendly_callback(self, msg):
        """Update friendly drone pose from PX4 odometry (includes orientation)"""
        # Store full pose with position and orientation
        self.friendly_pose = DronePose(
            x=msg.position[0],
            y=msg.position[1],
            z=msg.position[2]
        )
        # Note: VehicleOdometry also contains quaternion in msg.q for future use

    def detection_callback(self, msg):
        """Process enemy detection and transform to world coordinates"""
        # Need friendly pose to do coordinate transformation
        if self.friendly_pose is None:
            self.get_logger().warn_throttle(5.0, 'No friendly pose available for coordinate transformation')
            return

        # Create a DroneDetection-like object to pass to coordinate transform
        # (We need to import/create the DetectionResult type, but for now using the message directly)

        # Use the coordinate transform to convert to world coordinates
        enemy_world_pose = self.transform.camera_to_world_coordinates(msg, self.friendly_pose)

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