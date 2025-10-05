#!/usr/bin/env python3
"""
AirSim Camera Bridge for ROS2
Publishes camera images from AirSim to ROS2 topics
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import airsim
import numpy as np
import cv2


class AirSimCameraBridge(Node):
    def __init__(self):
        super().__init__('airsim_camera_bridge')

        # Parameters
        self.declare_parameter('host_ip', 'localhost')
        self.declare_parameter('vehicle_name', 'Ally')
        self.declare_parameter('camera_name', 'front_center')
        self.declare_parameter('publish_rate', 30.0)  # Hz
        self.declare_parameter('image_width', 640)
        self.declare_parameter('image_height', 480)
        self.declare_parameter('fov_degrees', 60.0)

        host_ip = self.get_parameter('host_ip').value
        self.vehicle_name = self.get_parameter('vehicle_name').value
        self.camera_name = self.get_parameter('camera_name').value
        publish_rate = self.get_parameter('publish_rate').value
        self.image_width = self.get_parameter('image_width').value
        self.image_height = self.get_parameter('image_height').value
        fov_degrees = self.get_parameter('fov_degrees').value

        # Connect to AirSim
        self.get_logger().info(f'Connecting to AirSim at {host_ip}...')
        self.client = airsim.MultirotorClient(ip=host_ip)
        self.client.confirmConnection()
        self.get_logger().info('Connected to AirSim successfully')

        # ROS2 Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)

        # CV Bridge for image conversion
        self.bridge = CvBridge()

        # Create timer for publishing at specified rate
        timer_period = 1.0 / publish_rate
        self.timer = self.create_timer(timer_period, self.publish_camera_data)

        # Camera info message (static, computed once)
        self.camera_info_msg = self.create_camera_info_msg(fov_degrees)

        self.get_logger().info(f'Publishing camera at {publish_rate} Hz from {self.vehicle_name}/{self.camera_name}')

    def create_camera_info_msg(self, fov_degrees):
        """Create camera info message with intrinsic parameters"""
        msg = CameraInfo()
        msg.header.frame_id = 'camera_link'
        msg.width = self.image_width
        msg.height = self.image_height

        # Calculate focal length from FOV
        # f = (image_width / 2) / tan(fov / 2)
        fov_rad = np.deg2rad(fov_degrees)
        fx = fy = (self.image_width / 2.0) / np.tan(fov_rad / 2.0)
        cx = self.image_width / 2.0
        cy = self.image_height / 2.0

        # Camera matrix K
        msg.k = [fx, 0.0, cx,
                 0.0, fy, cy,
                 0.0, 0.0, 1.0]

        # Distortion coefficients (assuming no distortion)
        msg.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        msg.distortion_model = 'plumb_bob'

        # Rectification matrix (identity for monocular)
        msg.r = [1.0, 0.0, 0.0,
                 0.0, 1.0, 0.0,
                 0.0, 0.0, 1.0]

        # Projection matrix
        msg.p = [fx, 0.0, cx, 0.0,
                 0.0, fy, cy, 0.0,
                 0.0, 0.0, 1.0, 0.0]

        return msg

    def publish_camera_data(self):
        """Fetch image from AirSim and publish to ROS2"""
        try:
            # Request RGB image from AirSim
            responses = self.client.simGetImages([
                airsim.ImageRequest(
                    self.camera_name,
                    airsim.ImageType.Scene,
                    False,
                    False
                )
            ], vehicle_name=self.vehicle_name)

            if len(responses) == 0:
                self.get_logger().warn('No image received from AirSim')
                return

            response = responses[0]

            # Convert to numpy array
            img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)

            # Reshape to image dimensions (AirSim returns RGB)
            img_rgb = img1d.reshape(response.height, response.width, 3)

            # Convert RGB to BGR for ROS (OpenCV convention)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

            # Create ROS Image message
            timestamp = self.get_clock().now().to_msg()
            image_msg = self.bridge.cv2_to_imgmsg(img_bgr, encoding='bgr8')
            image_msg.header.stamp = timestamp
            image_msg.header.frame_id = 'camera_link'

            # Update camera info timestamp
            self.camera_info_msg.header.stamp = timestamp

            # Publish
            self.image_pub.publish(image_msg)
            self.camera_info_pub.publish(self.camera_info_msg)

        except Exception as e:
            self.get_logger().error(f'Error publishing camera data: {str(e)}')


def main(args=None):
    rclpy.init(args=args)
    node = AirSimCameraBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
