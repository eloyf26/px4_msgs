import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from halcon1_prediction.predictor import Predictor
from halcon1_prediction.predictor.utils.kalman_filter import KalmanFilterParameters
from halcon1_prediction.predictor.utils.monte_carlo import MonteCarloParameters
from halcon1_types import DronePose

class PredictionNode(Node):
    def __init__(self):
        super().__init__('prediction_node')

        # Publishers
        self.trajectory_pub = self.create_publisher(
            Path, '/enemy/trajectory_prediction', 10)

        # Subscribers
        self.enemy_sub = self.create_subscription(
            PoseStamped, '/enemy/pose',
            self.enemy_callback, 10)

        # Algorithms
        self.predictor = Predictor(kf_params = KalmanFilterParameters(),
                                   mc_params = MonteCarloParameters())

    def enemy_callback(self, msg):
        """Process enemy pose and generate trajectory prediction"""
        enemy_pose = DronePose(
            x=msg.pose.position.x,
            y=msg.pose.position.y,
            z=msg.pose.position.z
        )
        timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        trajectory_prediction = self.predictor.predict(enemy_pose, timestamp)
        self.publish_prediction(trajectory_prediction, msg.header)

    def publish_prediction(self, trajectory_prediction, original_header):
        """Convert trajectory prediction to NavPath and publish"""
        path_msg = Path()
        path_msg.header.stamp = original_header.stamp
        path_msg.header.frame_id = 'world'

        # Convert trajectory prediction array to PoseStamped messages
        for timestamp, drone_pose in trajectory_prediction:
            pose_stamped = PoseStamped()
            pose_stamped.header.stamp.sec = int(timestamp)
            pose_stamped.header.stamp.nanosec = int((timestamp - int(timestamp)) * 1e9)
            pose_stamped.header.frame_id = 'world'

            pose_stamped.pose.position.x = drone_pose.x
            pose_stamped.pose.position.y = drone_pose.y
            pose_stamped.pose.position.z = drone_pose.z

            # Identity quaternion for orientation
            pose_stamped.pose.orientation.x = 0.0
            pose_stamped.pose.orientation.y = 0.0
            pose_stamped.pose.orientation.z = 0.0
            pose_stamped.pose.orientation.w = 1.0

            path_msg.poses.append(pose_stamped)

        self.trajectory_pub.publish(path_msg)

def main():
    rclpy.init()
    node = PredictionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()