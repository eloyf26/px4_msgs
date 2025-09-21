import rclpy
from rclpy.node import Node
from halcon1_msgs.msg import TrackedObject, PredictedTrajectory

class PredictionNode(Node):
    def __init__(self):
        super().__init__('prediction_node')
        self.sub = self.create_subscription(TrackedObject, '/enemy/tracked', self.track_callback, 10)
        self.pub = self.create_publisher(PredictedTrajectory, '/enemy/predicted', 10)

    def track_callback(self, msg):
        pred = PredictedTrajectory()
        pred.times = [1.0, 2.0, 3.0]
        pred.x = [msg.x + msg.vx, msg.x + 2*msg.vx, msg.x + 3*msg.vx]
        pred.y = [msg.y + msg.vy, msg.y + 2*msg.vy, msg.y + 3*msg.vy]
        pred.z = [msg.z + msg.vz, msg.z + 2*msg.vz, msg.z + 3*msg.vz]
        self.pub.publish(pred)

def main():
    rclpy.init()
    node = PredictionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()