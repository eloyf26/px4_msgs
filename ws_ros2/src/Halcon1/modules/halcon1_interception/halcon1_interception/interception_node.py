import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
import numpy as np
from halcon1_msgs.msg import TrajectoryWithUncertainty, EnemyPose
from px4_msgs.msg import TrajectorySetpoint, VehicleLocalPosition, OffboardControlMode
from halcon1_interception.trajectory_planner import TrajectoryPlanner
from halcon1_interception.px4_command_generator import PX4CommandGenerator

class InterceptionNode(Node):
    def __init__(self):
        super().__init__('interception_node')
        self.get_logger().info('Starting simplified interception node...')

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

        # Subscribers
        self.trajectory_sub = self.create_subscription(
            TrajectoryWithUncertainty, '/enemy/predicted_trajectory',
            self.trajectory_callback, 10)
        self.friendly_sub = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position',
            self.friendly_callback, qos_profile)
        self.enemy_pose_sub = self.create_subscription(
            EnemyPose, '/enemy/pose',
            self.enemy_callback, 10)

        # Algorithms
        self.planner = TrajectoryPlanner()
        self.command_generator = PX4CommandGenerator()

        # State
        self.friendly_position = np.array([0.0, 0.0, 0.0])
        self.friendly_velocity = np.array([0.0, 0.0, 0.0])
        self.enemy_position = np.array([10.0, 5.0, -5.0])
        self.trajectory_start_time = None
        self.interception_active = False

        # Timer for 50Hz publishing
        self.timer = self.create_timer(0.02, self.publish_command)

        self.get_logger().info('Interception node ready. Arm and takeoff manually via QGroundControl.')
        self.get_logger().info('Once airborne, the system will automatically intercept detected enemies.')

    def friendly_callback(self, msg):
        """Update friendly drone position from PX4"""
        if msg.xy_valid and msg.z_valid:
            self.friendly_position = np.array([msg.x, msg.y, msg.z])
        if msg.v_xy_valid and msg.v_z_valid:
            self.friendly_velocity = np.array([msg.vx, msg.vy, msg.vz])

    def enemy_callback(self, msg):
        """Update enemy position for interception check"""
        self.enemy_position = np.array([msg.x, msg.y, msg.z])

    def trajectory_callback(self, msg):
        """Process predicted trajectory and plan interception"""
        # Only process if we have valid trajectory data
        if len(msg.times) == 0:
            return

        # Convert to internal format
        enemy_trajectory = {
            'times': np.array(msg.times),
            'mean': np.column_stack([msg.mean_x, msg.mean_y, msg.mean_z]),
            'upper': np.column_stack([msg.upper_x, msg.upper_y, msg.upper_z]),
            'lower': np.column_stack([msg.lower_x, msg.lower_y, msg.lower_z])
        }

        # Plan interception
        trajectory = self.planner.plan_interception(
            enemy_trajectory,
            self.friendly_position,
            self.friendly_velocity
        )

        if trajectory is not None:
            self.command_generator.set_trajectory(trajectory)
            self.trajectory_start_time = self.get_clock().now()
            self.interception_active = True

            # Log interception details
            distance_to_enemy = np.linalg.norm(self.friendly_position - self.enemy_position)
            self.get_logger().info(f'📍 Interception planned! Enemy distance: {distance_to_enemy:.1f}m')

    def publish_command(self):
        """Publish commands at 50Hz"""
        # Always publish offboard control mode
        offboard_msg = OffboardControlMode()
        offboard_msg.position = True
        offboard_msg.velocity = True
        offboard_msg.acceleration = True
        offboard_msg.attitude = False
        offboard_msg.body_rate = False
        offboard_msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_mode_pub.publish(offboard_msg)

        # Publish trajectory setpoint
        msg = TrajectorySetpoint()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)

        if self.interception_active and self.trajectory_start_time is not None:
            # Get current trajectory setpoint
            time_diff = self.get_clock().now() - self.trajectory_start_time
            current_time = time_diff.nanoseconds / 1e9

            setpoint = self.command_generator.get_setpoint(current_time)

            if setpoint is not None:
                msg.position = setpoint['position']
                msg.velocity = setpoint['velocity']
                msg.acceleration = setpoint['acceleration']
                msg.yaw = setpoint['yaw']
                msg.yawspeed = setpoint['yawspeed']

                # Check interception success
                distance_to_enemy = np.linalg.norm(self.friendly_position - self.enemy_position)
                if distance_to_enemy < 0.5:
                    self.get_logger().info(f'✅ INTERCEPTION SUCCESSFUL! Distance: {distance_to_enemy:.2f}m')
                    self.interception_active = False
            else:
                # Trajectory complete
                self.interception_active = False
                self.get_logger().info('Interception trajectory complete')

                # Hover at current position
                msg.position = self.friendly_position.tolist()
                msg.velocity = [float('nan')] * 3
                msg.acceleration = [float('nan')] * 3
                msg.yaw = float('nan')
                msg.yawspeed = float('nan')
        else:
            # No active interception - maintain current position
            msg.position = self.friendly_position.tolist()
            msg.velocity = [float('nan')] * 3
            msg.acceleration = [float('nan')] * 3
            msg.yaw = float('nan')
            msg.yawspeed = float('nan')

        self.setpoint_pub.publish(msg)

def main():
    rclpy.init()
    node = InterceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()