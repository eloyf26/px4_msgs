import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from halcon1_msgs.msg import DroneDetection
from halcon1_detection.detection_algorithm import DetectionAlgorithm

class DetectionNode(Node):
    def __init__(self):
        super().__init__('detection_node')

        # Publishers
        self.detection_pub = self.create_publisher(DroneDetection, '/enemy/detection', 10)
        self.debug_image_pub = self.create_publisher(Image, '/debug/ally/detection_image', 10)

        # Subscriber for camera images (use standard sensor QoS)
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10  # Use default QoS for sensor data
        )

        # Detection algorithm and CV bridge
        self.algorithm = DetectionAlgorithm()
        self.bridge = CvBridge()

        # Statistics
        self.frame_count = 0
        self.detection_count = 0

        self.get_logger().info('Detection node initialized')
        self.get_logger().info('Subscribing to: /camera/image')
        self.get_logger().info('Publishing detections to: /enemy/detection')
        self.get_logger().info('Publishing debug images to: /debug/ally/detection_image')

    def image_callback(self, image_msg):
        """Process incoming camera image and detect enemy drones"""
        self.frame_count += 1

        try:
            # Convert ROS image to OpenCV format (BGR)
            cv_image = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f'Failed to convert image: {e}')
            return

        # Run detection algorithm on the image
        # Returns both detection result and annotated image
        detection_result, annotated_image = self.algorithm.detect(cv_image)

        # Check if we have a valid detection
        if detection_result.width > 0 and detection_result.height > 0:
            self.detection_count += 1
            self.get_logger().debug(
                f'Detection #{self.detection_count}: '
                f'Processing space bbox=({detection_result.x}, {detection_result.y}, '
                f'{detection_result.width}, {detection_result.height})'
            )

            # Create DroneDetection message ONLY for valid detections
            # NOTE: YOLO returns coordinates in original image space (1280x960)
            # No scaling needed - coordinates already match camera resolution!
            detection_msg = DroneDetection()
            detection_msg.header.stamp = self.get_clock().now().to_msg()
            detection_msg.header.frame_id = 'camera'
            detection_msg.x = float(detection_result.x)
            detection_msg.y = float(detection_result.y)
            detection_msg.width = float(detection_result.width)
            detection_msg.height = float(detection_result.height)

            # Log coordinates for debugging
            self.get_logger().debug(
                f'Camera space bbox: ({detection_msg.x:.1f}, {detection_msg.y:.1f}, '
                f'{detection_msg.width:.1f}, {detection_msg.height:.1f})'
            )

            # Publish detection
            self.detection_pub.publish(detection_msg)
        else:
            # No valid detection - log this for debugging
            self.get_logger().debug(f'No detection in frame {self.frame_count}')

        # Convert annotated image back to ROS message and publish
        try:
            debug_msg = self.bridge.cv2_to_imgmsg(annotated_image, encoding='bgr8')
            debug_msg.header = image_msg.header  # Preserve original header
            self.debug_image_pub.publish(debug_msg)
        except CvBridgeError as e:
            self.get_logger().error(f'Failed to convert debug image: {e}')

        # Periodic status update
        if self.frame_count % 30 == 0:
            self.get_logger().info(
                f'Processed {self.frame_count} frames, '
                f'{self.detection_count} detections'
            )

def main():
    rclpy.init()
    node = DetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()