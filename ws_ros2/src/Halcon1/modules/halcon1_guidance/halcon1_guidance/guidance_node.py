import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import TrajectorySetpoint, VehicleOdometry, OffboardControlMode, VehicleCommand
from geometry_msgs.msg import PoseStamped
import numpy as np

from halcon1_guidance.utils.pro_nav import ProportionalNavigationParameters
from halcon1_guidance.utils.kalman_filter import KalmanFilterParameters
from halcon1_guidance.state_manager import StateManager

from halcon1_guidance.px4_command_generator import PX4CommandGenerator


class GuidanceNode(Node):
    def __init__(self):
        super().__init__('guidance_node')
        self.get_logger().info('Starting guidance node...')

        # Configure QoS profile for PX4
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Publishers
        self.setpoint_pub = self.create_publisher(
            TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.offboard_mode_pub = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.vehicle_command_publisher = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos_profile)

        # Subscribers
        self.friendly_sub = self.create_subscription(
            VehicleOdometry, '/fmu/out/vehicle_odometry',
            self.friendly_callback, qos_profile)
        self.enemy_pose_sub = self.create_subscription(
            PoseStamped, '/enemy/pose',
            self.enemy_callback, 10)

        # Algorithms
        self.state_manager = StateManager(KalmanFilterParameters(process_noise = 0.1),
                                          ProportionalNavigationParameters(navigation_constant = 3.0, max_acceleration = 10.0,
                                                                           max_velocity = 20.0, directional_to_los_change_threshold = 50.0),
                                          interception_range = 0.5, offset_m = 0.0)

        # Timer for 50 Hz publishing (PX4 requirements)
        self.timer = self.create_timer(0.02, self.publish_command)

        # Offboard control mode parameters
        self.min_offboard_counter = 10 # Arbitrary number to ensure vehicle receives offboard control mode signals before changing to offboard mode
        self.offboard_counter = 0

        # Timer for offboard control mode publishing (10 Hz)
        self.offboard_timer = self.create_timer(0.1, self.publish_control)

        self.get_logger().info('Guidance node ready. Arm and takeoff manually via QGroundControl.')
        self.get_logger().info('Once airborne, the system will automatically intercept detected enemies.')

    def friendly_callback(self, msg):
        """Update friendly drone position from PX4"""
        time_millis = int(self.get_clock().now().nanoseconds / 1000)
        self.state_manager.update_friendly(friendly_position=np.array(msg.position),
                                  friendly_velocity=np.array(msg.velocity),
                                  current_time_millis=time_millis)

    def enemy_callback(self, msg):
        """Update enemy position for guidance check"""
        time_millis = int(self.get_clock().now().nanoseconds / 1000)
        self.state_manager.update_enemy(enemy_position=np.array([msg.pose.position.x, msg.pose.position.y, msg.pose.position.z]),
                                        current_time_millis=time_millis)

    def publish_control(self):
        """Publish offboard control mode to PX4"""
        current_time_millis = int(self.get_clock().now().nanoseconds / 1000)
        offboard_message = PX4CommandGenerator.generate_offboard_message(current_time_millis)
        self.offboard_mode_pub.publish(offboard_message)

        # Send initial offboard commands
        if self.offboard_counter < self.min_offboard_counter:
            self.offboard_counter += 1
            if self.offboard_counter == self.min_offboard_counter:
                self.get_logger().info('Sending command to switch to OFFBOARD mode and arm the vehicle.')
                set_offboard_mode_command = PX4CommandGenerator.generate_set_offboard_mode_command(current_time_millis)
                self.vehicle_command_publisher.publish(set_offboard_mode_command)

    def publish_command(self):
        """Publish trajectory setpoint and offboard mode to PX4"""
        # Ensure we have valid positions
        if self.state_manager.friendly_position is None or self.state_manager.enemy_last_update is None:
            return

        # Update state manager
        current_time_millis = int(self.get_clock().now().nanoseconds / 1000)
        current_acceleration = self.state_manager.update(current_time_millis)

        # Generate offboard commands and trajectory setpoint
        trajectory_message = PX4CommandGenerator.generate_trajectory_message(
            current_acceleration,
            current_time_millis
        )

        # Publish message
        self.setpoint_pub.publish(trajectory_message)

def main():
    rclpy.init()
    node = GuidanceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()