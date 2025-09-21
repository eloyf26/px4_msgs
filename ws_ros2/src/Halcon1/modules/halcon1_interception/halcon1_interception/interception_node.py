import rclpy
from rclpy.node import Node
from halcon1_msgs.msg import PredictedTrajectory, InterceptionCommand

class InterceptionNode(Node):
    def __init__(self):
        super().__init__('interception_node')
        self.sub = self.create_subscription(PredictedTrajectory, '/enemy/predicted', self.predict_callback, 10)
        self.pub = self.create_publisher(InterceptionCommand, '/interception/command', 10)

    def predict_callback(self, msg):
        cmd = InterceptionCommand()
        if len(msg.x) > 0:
            cmd.target_x = msg.x[0]
            cmd.target_y = msg.y[0]
            cmd.target_z = msg.z[0]
        self.pub.publish(cmd)

def main():
    rclpy.init()
    node = InterceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()