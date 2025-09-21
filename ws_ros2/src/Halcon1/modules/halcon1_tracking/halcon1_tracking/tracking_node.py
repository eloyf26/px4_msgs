import rclpy
from rclpy.node import Node
import numpy as np
from halcon1_msgs.msg import DroneDetection, EnemyPose
from px4_msgs.msg import VehicleLocalPosition, VehicleOdometry
from halcon1_tracking.coordinate_transform import CoordinateTransform
from std_msgs.msg import Header

class TrackingNode(Node):
    def __init__(self):
        super().__init__('tracking_node')

        # Publishers
        self.enemy_pub = self.create_publisher(EnemyPose, '/enemy/pose', 10)

        # Subscribers
        self.detection_sub = self.create_subscription(
            DroneDetection, '/enemy/detection',
            self.detection_callback, 10)
        self.friendly_sub = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position',
            self.friendly_callback, 10)

        # Coordinate transform
        self.transform = CoordinateTransform()

        # State
        self.friendly_position = np.array([0.0, 0.0, 0.0])
        self.friendly_velocity = np.array([0.0, 0.0, 0.0])
        self.last_enemy_position = None
        self.last_detection_time = None

    def friendly_callback(self, msg):
        """Update friendly drone position from PX4"""
        if msg.xy_valid and msg.z_valid:
            self.friendly_position = np.array([msg.x, msg.y, msg.z])
        if msg.v_xy_valid and msg.v_z_valid:
            self.friendly_velocity = np.array([msg.vx, msg.vy, msg.vz])

    def detection_callback(self, msg):
        """Process enemy detection and transform to world coordinates"""
        # Only process valid detections
        if msg.confidence < 0.5:
            return

        # Transform pixel detection to world NED coordinates
        enemy_pos_ned = self.transform.pixel_to_world_ned(
            msg.x, msg.y,
            self.friendly_position,
            estimated_distance=15.0  # Fixed distance estimate for now
        )

        # Estimate velocity from position change
        current_time = self.get_clock().now()
        if self.last_enemy_position is not None and self.last_detection_time is not None:
            dt = (current_time - self.last_detection_time).nanoseconds / 1e9
            if dt > 0:
                velocity = (enemy_pos_ned - self.last_enemy_position) / dt
            else:
                velocity = np.array([0.0, 0.0, 0.0])
        else:
            velocity = np.array([0.0, 0.0, 0.0])

        # Update state
        self.last_enemy_position = enemy_pos_ned
        self.last_detection_time = current_time

        # Publish enemy pose
        enemy_msg = EnemyPose()
        enemy_msg.header = Header()
        enemy_msg.header.stamp = current_time.to_msg()
        enemy_msg.header.frame_id = 'world_ned'

        enemy_msg.x = enemy_pos_ned[0]
        enemy_msg.y = enemy_pos_ned[1]
        enemy_msg.z = enemy_pos_ned[2]
        enemy_msg.vx = velocity[0]
        enemy_msg.vy = velocity[1]
        enemy_msg.vz = velocity[2]

        # Simple covariance (diagonal)
        enemy_msg.covariance = [0.0] * 36
        enemy_msg.covariance[0] = 1.0  # x variance
        enemy_msg.covariance[7] = 1.0  # y variance
        enemy_msg.covariance[14] = 1.0  # z variance
        enemy_msg.covariance[21] = 2.0  # vx variance
        enemy_msg.covariance[28] = 2.0  # vy variance
        enemy_msg.covariance[35] = 2.0  # vz variance

        self.enemy_pub.publish(enemy_msg)

def main():
    rclpy.init()
    node = TrackingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()