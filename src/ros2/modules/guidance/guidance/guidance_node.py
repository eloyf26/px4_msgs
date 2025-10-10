import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import TrajectorySetpoint, VehicleOdometry, OffboardControlMode, VehicleCommand
from geometry_msgs.msg import PoseStamped
import numpy as np

from algorithms.pro_nav import ProportionalNavigationParameters
from algorithms.kalman_filter import KalmanFilterParameters
from guidance.state_manager import StateManager

from guidance.px4_command_generator import PX4CommandGenerator
from transforms import CoordinateTransform
from common_types import DronePose


class GuidanceNode(Node):
    def __init__(self):
        super().__init__('guidance_node')
        self.get_logger().info('Starting guidance node...')

        # Declare and get debug parameter
        self.declare_parameter('debug', False)
        self.debug_mode = self.get_parameter('debug').get_parameter_value().bool_value

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

        # Debug publisher (only created if debug mode is enabled)
        if self.debug_mode:
            self.debug_kf_prediction_pub = self.create_publisher(PoseStamped, '/debug/enemy/kf_prediction', 10)
        else:
            self.debug_kf_prediction_pub = None

        # Subscribers
        self.friendly_sub = self.create_subscription(
            VehicleOdometry, '/fmu/out/vehicle_odometry',
            self.friendly_callback, qos_profile)
        self.enemy_pose_sub = self.create_subscription(
            PoseStamped, '/enemy/pose',
            self.enemy_callback, 10)

        # Algorithms
        self.state_manager = StateManager(KalmanFilterParameters(),
                                          ProportionalNavigationParameters(),
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
        self.get_logger().info(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        if self.debug_mode:
            self.get_logger().info('\tKF prediction will be published to /debug/enemy/kf_prediction topic.')

    def friendly_callback(self, msg):
        """Update friendly drone position from PX4"""
        # Transform position and velocity from NED (PX4) to ENU (ROS2/state_manager)
        # Use message timestamp for accurate state estimation (convert microseconds to milliseconds)
        time_millis = msg.timestamp / 1000.0

        friendly_position_enu = CoordinateTransform.ned_to_enu_local_frame(msg.position)
        friendly_velocity_enu = CoordinateTransform.ned_to_enu_local_frame(msg.velocity)

        self.state_manager.update_friendly(
            friendly_position=np.array([friendly_position_enu.x, friendly_position_enu.y, friendly_position_enu.z]),
            friendly_velocity=np.array([friendly_velocity_enu.x, friendly_velocity_enu.y, friendly_velocity_enu.z]),
            current_time_millis=time_millis
        )

    def enemy_callback(self, msg):
        """Update enemy position for guidance check"""
        # Use message timestamp for accurate state estimation (convert to milliseconds)
        time_millis = msg.header.stamp.sec * 1000.0 + msg.header.stamp.nanosec / 1e6

        enemy_position = np.array([msg.pose.position.x, msg.pose.position.y, msg.pose.position.z])
        self.get_logger().info(
            f'Enemy position (ENU): x={enemy_position[0]:.3f}, '
            f'y={enemy_position[1]:.3f}, z={enemy_position[2]:.3f} m'
        )

        self.state_manager.update_enemy(enemy_position=enemy_position,
                                        current_time_millis=time_millis)

    def publish_control(self):
        """Publish offboard control mode to PX4"""
        current_time_micros = int(self.get_clock().now().nanoseconds / 1000)  # Keep in microseconds for PX4
        offboard_message = PX4CommandGenerator.generate_offboard_message(current_time_micros)
        self.offboard_mode_pub.publish(offboard_message)

        # Send initial offboard commands
        if self.offboard_counter < self.min_offboard_counter:
            self.offboard_counter += 1
            if self.offboard_counter == self.min_offboard_counter:
                self.get_logger().info('Sending command to switch to OFFBOARD mode.')
                set_offboard_mode_command = PX4CommandGenerator.generate_set_offboard_mode_command(current_time_micros)
                self.vehicle_command_publisher.publish(set_offboard_mode_command)

    def publish_command(self):
        """Publish trajectory setpoint to PX4"""
        # Ensure we have valid positions
        if self.state_manager.friendly_position is None or self.state_manager.enemy_last_update is None:
            return

        # Update state manager (convert nanoseconds to milliseconds for state estimation)
        current_time_millis = self.get_clock().now().nanoseconds / 1e6
        current_acceleration, enemy_predicted_position = self.state_manager.update(current_time_millis)

        if self.debug_mode and enemy_predicted_position is not None and self.debug_kf_prediction_pub is not None:
            # Publish KF predicted enemy position for debugging
            kf_prediction_msg = PoseStamped()
            kf_prediction_msg.header.stamp = self.get_clock().now().to_msg()
            kf_prediction_msg.header.frame_id = 'world'
            kf_prediction_msg.pose.position.x = enemy_predicted_position[0]
            kf_prediction_msg.pose.position.y = enemy_predicted_position[1]
            kf_prediction_msg.pose.position.z = enemy_predicted_position[2]
            self.debug_kf_prediction_pub.publish(kf_prediction_msg)

        # Log acceleration for debugging
        if current_acceleration is None:
            self.get_logger().info('No valid acceleration command computed')
            return

        # Convert acceleration from ENU (state_manager) to NED (PX4)
        acceleration_enu = DronePose(x=current_acceleration[0], y=current_acceleration[1], z=current_acceleration[2])
        acceleration_ned = CoordinateTransform.enu_to_ned_local_frame(acceleration_enu)

        # Generate offboard commands and trajectory setpoint (convert back to microseconds for PX4)
        current_time_micros = int(self.get_clock().now().nanoseconds / 1000)
        trajectory_message = PX4CommandGenerator.generate_trajectory_message(
            np.array(acceleration_ned),
            current_time_micros
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