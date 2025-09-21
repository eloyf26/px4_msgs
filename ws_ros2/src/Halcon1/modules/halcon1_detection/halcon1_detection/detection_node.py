import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
import numpy as np
from halcon1_msgs.msg import DroneDetection
from px4_msgs.msg import VehicleLocalPosition, VehicleOdometry, VehicleControlMode
from halcon1_detection.detection_algorithm import DetectionAlgorithm

class DetectionNode(Node):
    def __init__(self):
        super().__init__('detection_node')

        # Publisher
        self.pub = self.create_publisher(DroneDetection, '/enemy/detection', 10)

        # QoS profile for PX4 topics
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Subscribers
        self.friendly_sub = self.create_subscription(
            VehicleLocalPosition,
            '/fmu/out/vehicle_local_position',
            self.friendly_callback,
            qos_profile
        )
        self.vehicle_status_sub = self.create_subscription(
            VehicleControlMode,
            '/fmu/out/vehicle_control_mode',
            self.vehicle_status_callback,
            qos_profile
        )

        # Detection algorithm
        self.algorithm = DetectionAlgorithm()

        # State
        self.friendly_position = np.array([0.0, 0.0, 0.0])
        self.friendly_quaternion = None  # Could get from VehicleOdometry if needed
        self.is_armed = False
        self.enemy_started = False

        # Timer for detection at 10Hz
        self.timer = self.create_timer(0.1, self.publish_detection)

        self.get_logger().info('Detection node ready. Enemy will appear when drone is armed.')

    def friendly_callback(self, msg):
        """Update friendly drone position from PX4"""
        if msg.xy_valid and msg.z_valid:
            self.friendly_position = np.array([msg.x, msg.y, msg.z])

    def vehicle_status_callback(self, msg):
        """Update vehicle status from PX4"""
        was_armed = self.is_armed
        self.is_armed = msg.flag_armed

        if not was_armed and self.is_armed and not self.enemy_started:
            self.get_logger().info('🚁 Drone armed! Enemy drone activated.')
            self.enemy_started = True

    def publish_detection(self):
        """Generate detection based on friendly drone position"""
        # Don't detect enemy until drone is armed
        if not self.is_armed:
            return

        # Use ROS2 simulation time
        current_time_sec = self.get_clock().now().nanoseconds / 1e9

        x, y, confidence = self.algorithm.detect(
            self.friendly_position,
            self.friendly_quaternion,
            current_time_sec
        )

        msg = DroneDetection()
        msg.x = float(x)  # Convert numpy float to Python float
        msg.y = float(y)
        msg.confidence = float(confidence)
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = DetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()