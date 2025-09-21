import rclpy
from rclpy.node import Node
from halcon1_msgs.msg import DroneDetection, TrackedObject

class TrackingNode(Node):
    def __init__(self):
        super().__init__('tracking_node')
        self.sub = self.create_subscription(DroneDetection, '/enemy/detection', self.detection_callback, 10)
        self.pub = self.create_publisher(TrackedObject, '/enemy/tracked', 10)

    def detection_callback(self, msg):
        tracked = TrackedObject()
        tracked.x = msg.x / 100.0
        tracked.y = msg.y / 100.0
        tracked.z = 10.0
        tracked.vx = 1.0
        tracked.vy = 0.0
        tracked.vz = 0.0
        self.pub.publish(tracked)

def main():
    rclpy.init()
    node = TrackingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()