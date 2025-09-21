import rclpy
from rclpy.node import Node
from halcon1_msgs.msg import DroneDetection
import math

class DetectionNode(Node):
    def __init__(self):
        super().__init__('detection_node')
        self.pub = self.create_publisher(DroneDetection, '/enemy/detection', 10)
        self.timer = self.create_timer(0.1, self.publish_detection)
        self.time = 0.0

    def publish_detection(self):
        msg = DroneDetection()
        msg.x = 320.0 + 50.0 * math.sin(self.time * 0.5)
        msg.y = 240.0 + 30.0 * math.cos(self.time * 0.3)
        msg.confidence = 0.95
        self.pub.publish(msg)
        self.time += 0.1

def main():
    rclpy.init()
    node = DetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()