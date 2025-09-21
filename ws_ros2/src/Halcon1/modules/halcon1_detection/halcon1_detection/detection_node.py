import rclpy
from rclpy.node import Node
import numpy as np
from halcon1_msgs.msg import DroneDetection
from px4_msgs.msg import VehicleLocalPosition, VehicleOdometry
from halcon1_detection.detection_algorithm import DetectionAlgorithm

class DetectionNode(Node):
    def __init__(self):
        super().__init__('detection_node')

        # Publisher
        self.pub = self.create_publisher(DroneDetection, '/enemy/detection', 10)

        # Subscriber for friendly drone position
        self.friendly_sub = self.create_subscription(
            VehicleLocalPosition,
            '/fmu/out/vehicle_local_position',
            self.friendly_callback,
            10
        )

        # Detection algorithm
        self.algorithm = DetectionAlgorithm()

        # State
        self.friendly_position = np.array([0.0, 0.0, 0.0])
        self.friendly_quaternion = None  # Could get from VehicleOdometry if needed

        # Timer for detection at 10Hz
        self.timer = self.create_timer(0.1, self.publish_detection)

    def friendly_callback(self, msg):
        """Update friendly drone position from PX4"""
        if msg.xy_valid and msg.z_valid:
            self.friendly_position = np.array([msg.x, msg.y, msg.z])

    def publish_detection(self):
        """Generate detection based on friendly drone position"""
        # Use ROS2 simulation time
        current_time_sec = self.get_clock().now().nanoseconds / 1e9

        x, y, confidence = self.algorithm.detect(
            self.friendly_position,
            self.friendly_quaternion,
            current_time_sec
        )

        msg = DroneDetection()
        msg.x = x
        msg.y = y
        msg.confidence = confidence
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = DetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()