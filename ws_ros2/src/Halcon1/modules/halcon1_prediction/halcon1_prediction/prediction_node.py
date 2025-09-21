import rclpy
from rclpy.node import Node
import numpy as np
from halcon1_msgs.msg import EnemyPose, TrajectoryWithUncertainty
from halcon1_prediction.kalman_filter import KalmanFilter
from halcon1_prediction.monte_carlo import MonteCarloPredictor
from std_msgs.msg import Header

class PredictionNode(Node):
    def __init__(self):
        super().__init__('prediction_node')

        # Publishers
        self.trajectory_pub = self.create_publisher(
            TrajectoryWithUncertainty, '/enemy/predicted_trajectory', 10)

        # Subscribers
        self.enemy_sub = self.create_subscription(
            EnemyPose, '/enemy/pose',
            self.enemy_callback, 10)

        # Algorithms
        self.kalman = KalmanFilter(dt=0.1)
        self.monte_carlo = MonteCarloPredictor(num_samples=100)

        # Timer for predictions at 5Hz
        self.predict_timer = self.create_timer(0.2, self.publish_prediction)

        # State
        self.current_state = None
        self.current_covariance = None

    def enemy_callback(self, msg):
        """Process enemy pose through Kalman filter"""
        # Create measurement vector
        measurement = np.array([
            msg.x, msg.y, msg.z,
            msg.vx, msg.vy, msg.vz
        ])

        # Create measurement covariance from message
        cov_matrix = np.array(msg.covariance).reshape(6, 6)

        # Predict step
        self.kalman.predict()

        # Update step
        state, covariance = self.kalman.update(measurement, cov_matrix)

        # Store for prediction
        self.current_state = state
        self.current_covariance = covariance

    def publish_prediction(self):
        """Generate and publish trajectory prediction"""
        if self.current_state is None:
            return

        # Generate Monte Carlo predictions
        predictions = self.monte_carlo.predict_trajectories(
            self.current_state,
            self.current_covariance,
            time_horizon=5.0,
            dt=0.5
        )

        # Create message
        msg = TrajectoryWithUncertainty()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'world_ned'

        # Time points
        msg.times = predictions['times'].tolist()

        # Mean trajectory
        msg.mean_x = predictions['mean'][:, 0].tolist()
        msg.mean_y = predictions['mean'][:, 1].tolist()
        msg.mean_z = predictions['mean'][:, 2].tolist()

        # Upper bounds
        msg.upper_x = predictions['upper'][:, 0].tolist()
        msg.upper_y = predictions['upper'][:, 1].tolist()
        msg.upper_z = predictions['upper'][:, 2].tolist()

        # Lower bounds
        msg.lower_x = predictions['lower'][:, 0].tolist()
        msg.lower_y = predictions['lower'][:, 1].tolist()
        msg.lower_z = predictions['lower'][:, 2].tolist()

        # Confidence level
        msg.confidence_level = 0.95

        self.trajectory_pub.publish(msg)

def main():
    rclpy.init()
    node = PredictionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()