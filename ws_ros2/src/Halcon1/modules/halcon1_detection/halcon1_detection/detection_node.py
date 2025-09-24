import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from halcon1_msgs.msg import DroneDetection
from halcon1_detection.detection_algorithm import DetectionAlgorithm

class DetectionNode(Node):
    def __init__(self):
        super().__init__('detection_node')

        # Publisher for detections
        self.detection_pub = self.create_publisher(DroneDetection, '/enemy/detection', 10)

        # Subscriber for camera images (use standard sensor QoS)
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10  # Use default QoS for sensor data
        )

        # Detection algorithm
        self.algorithm = DetectionAlgorithm()

        self.get_logger().info('Detection node initialized - waiting for camera images...')

    def image_callback(self, image_msg):
        """Process incoming camera image and detect enemy drones"""
        # Run detection algorithm on the image
        detection_result = self.algorithm.detect(image_msg)

        # Create DroneDetection message
        detection_msg = DroneDetection()
        detection_msg.header.stamp = self.get_clock().now().to_msg()
        detection_msg.header.frame_id = 'camera'
        detection_msg.x = float(detection_result.x)
        detection_msg.y = float(detection_result.y)
        detection_msg.width = float(detection_result.width)
        detection_msg.height = float(detection_result.height)

        # Publish detection
        self.detection_pub.publish(detection_msg)

def main():
    rclpy.init()
    node = DetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()