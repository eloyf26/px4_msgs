#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import VehicleLocalPosition, TrajectorySetpoint, VehicleStatus, VehicleOdometry
from geometry_msgs.msg import PoseStamped, TwistStamped, Vector3Stamped
from nav_msgs.msg import Path, Odometry
from std_msgs.msg import Header, String, Int32
import math


class PX4DebugTranslator(Node):
    """Translates PX4 messages to standard ROS2 types for visualization and debugging."""

    def __init__(self):
        super().__init__('px4_debug_translator')

        self.get_logger().info('PX4 Debug Translator starting...')

        # Configure QoS profile for PX4
        self.px4_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=0
        )

        # Standard QoS for ROS2 topics
        self.ros_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Track both drones
        # Instance 0 uses no namespace for compatibility, instance 1 uses px4_1
        self.drones = [
            {'id': 0, 'namespace': '', 'name': 'ally'},
            {'id': 1, 'namespace': 'px4_1', 'name': 'enemy'}
        ]

        # Initialize paths for each drone
        self.paths = {}
        self.max_path_length = 1000

        # Setup subscribers and publishers for each drone
        for drone in self.drones:
            self.setup_drone_translators(drone)

        self.get_logger().info(f'PX4 Debug Translator initialized for {len(self.drones)} drones')
        self.get_logger().info('Available visualization topics:')
        self.get_logger().info('  - /debug/<drone_name>/pose (PoseStamped)')
        self.get_logger().info('  - /debug/<drone_name>/velocity (TwistStamped)')
        self.get_logger().info('  - /debug/<drone_name>/setpoint (PoseStamped)')
        self.get_logger().info('  - /debug/<drone_name>/path (Path)')
        self.get_logger().info('  - /debug/<drone_name>/odometry (Odometry)')
        self.get_logger().info('  - /debug/<drone_name>/status (String)')
        self.get_logger().info('  - /debug/<drone_name>/nav_state (Int32)')

    def setup_drone_translators(self, drone):
        """Setup subscribers and publishers for a single drone."""
        ns = drone['namespace']
        name = drone['name']

        # Initialize path for this drone
        self.paths[name] = Path()
        self.paths[name].header.frame_id = 'world'

        # Build topic prefix - empty for instance 0, /px4_1 for instance 1
        topic_prefix = f'/{ns}' if ns else ''

        # Subscribers
        self.create_subscription(
            VehicleLocalPosition,
            f'{topic_prefix}/fmu/out/vehicle_local_position_v1',
            lambda msg, n=name: self.position_callback(msg, n),
            self.px4_qos)

        self.create_subscription(
            TrajectorySetpoint,
            f'{topic_prefix}/fmu/in/trajectory_setpoint',
            lambda msg, n=name: self.setpoint_callback(msg, n),
            self.px4_qos)

        self.create_subscription(
            VehicleStatus,
            f'{topic_prefix}/fmu/out/vehicle_status_v1',
            lambda msg, n=name: self.status_callback(msg, n),
            self.px4_qos)

        self.create_subscription(
            VehicleOdometry,
            f'{topic_prefix}/fmu/out/vehicle_odometry_v1',
            lambda msg, n=name: self.odometry_callback(msg, n),
            self.px4_qos)

        # Publishers for visualization
        setattr(self, f'{name}_pose_pub', self.create_publisher(
            PoseStamped, f'/debug/{name}/pose', self.ros_qos))

        setattr(self, f'{name}_velocity_pub', self.create_publisher(
            TwistStamped, f'/debug/{name}/velocity', self.ros_qos))

        setattr(self, f'{name}_setpoint_pub', self.create_publisher(
            PoseStamped, f'/debug/{name}/setpoint', self.ros_qos))

        setattr(self, f'{name}_path_pub', self.create_publisher(
            Path, f'/debug/{name}/path', self.ros_qos))

        setattr(self, f'{name}_odom_pub', self.create_publisher(
            Odometry, f'/debug/{name}/odometry', self.ros_qos))

        setattr(self, f'{name}_status_pub', self.create_publisher(
            String, f'/debug/{name}/status', self.ros_qos))

        setattr(self, f'{name}_nav_state_pub', self.create_publisher(
            Int32, f'/debug/{name}/nav_state', self.ros_qos))

    def position_callback(self, msg, drone_name):
        """Convert VehicleLocalPosition to multiple ROS2 standard types."""
        # Create PoseStamped
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = 'world'

        # Position (NED to ENU: x=x, y=-y, z=-z)
        pose.pose.position.x = msg.x
        pose.pose.position.y = -msg.y
        pose.pose.position.z = -msg.z

        # Orientation from heading (yaw only, as VehicleLocalPosition doesn't have full quaternion)
        # Convert NED heading to ENU orientation
        yaw = -msg.heading + math.pi/2  # NED to ENU conversion
        pose.pose.orientation.w = math.cos(yaw/2)
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = math.sin(yaw/2)

        # Publish pose
        getattr(self, f'{drone_name}_pose_pub').publish(pose)

        # Create and publish TwistStamped for velocity
        twist = TwistStamped()
        twist.header = pose.header
        twist.twist.linear.x = msg.vx
        twist.twist.linear.y = -msg.vy  # NED to ENU
        twist.twist.linear.z = -msg.vz  # NED to ENU
        getattr(self, f'{drone_name}_velocity_pub').publish(twist)

        # Update path
        self.paths[drone_name].header.stamp = pose.header.stamp
        self.paths[drone_name].poses.append(pose)

        # Limit path length
        if len(self.paths[drone_name].poses) > self.max_path_length:
            self.paths[drone_name].poses.pop(0)

        # Publish path
        getattr(self, f'{drone_name}_path_pub').publish(self.paths[drone_name])

    def setpoint_callback(self, msg, drone_name):
        """Convert TrajectorySetpoint to PoseStamped."""
        try:
            pose = PoseStamped()
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.header.frame_id = 'world'

            # Position (NED to ENU)
            if hasattr(msg, 'position') and len(msg.position) >= 3:
                pose.pose.position.x = float(msg.position[0]) if not math.isnan(msg.position[0]) else 0.0
                pose.pose.position.y = float(-msg.position[1]) if not math.isnan(msg.position[1]) else 0.0
                pose.pose.position.z = float(-msg.position[2]) if not math.isnan(msg.position[2]) else 0.0

            # Default orientation (can be enhanced if yaw is available)
            pose.pose.orientation.w = 1.0
            pose.pose.orientation.x = 0.0
            pose.pose.orientation.y = 0.0
            pose.pose.orientation.z = 0.0

            getattr(self, f'{drone_name}_setpoint_pub').publish(pose)
        except Exception as e:
            self.get_logger().error(f"Error in setpoint_callback for {drone_name}: {e}")

    def status_callback(self, msg, drone_name):
        """Convert VehicleStatus to readable string and nav state."""
        # Navigation states
        nav_states = {
            0: "MANUAL", 1: "ALTCTL", 2: "POSCTL", 3: "AUTO_MISSION",
            4: "AUTO_LOITER", 5: "AUTO_RTL", 14: "OFFBOARD",
            7: "STAB", 8: "AUTO_TAKEOFF", 9: "AUTO_LAND",
            10: "AUTO_FOLLOW_TARGET", 11: "AUTO_PRECISION_LAND"
        }

        # Arming states
        arm_states = {
            0: "INIT", 1: "STANDBY", 2: "ARMED",
            3: "STANDBY_ERROR", 4: "SHUTDOWN", 5: "IN_AIR_RESTORE"
        }

        nav_state_str = nav_states.get(msg.nav_state, f"UNKNOWN({msg.nav_state})")
        arm_state_str = arm_states.get(msg.arming_state, f"UNKNOWN({msg.arming_state})")

        # Create status string
        status_msg = String()
        status_msg.data = f"NAV: {nav_state_str} | ARM: {arm_state_str}"
        getattr(self, f'{drone_name}_status_pub').publish(status_msg)

        # Publish nav state as integer for plotting
        nav_state_msg = Int32()
        nav_state_msg.data = msg.nav_state
        getattr(self, f'{drone_name}_nav_state_pub').publish(nav_state_msg)

    def odometry_callback(self, msg, drone_name):
        """Convert VehicleOdometry to nav_msgs/Odometry."""
        try:
            odom = Odometry()
            odom.header.stamp = self.get_clock().now().to_msg()
            odom.header.frame_id = 'world'
            odom.child_frame_id = f'{drone_name}_base_link'

            # Position (NED to ENU)
            if hasattr(msg, 'position') and len(msg.position) >= 3:
                odom.pose.pose.position.x = msg.position[0]
                odom.pose.pose.position.y = -msg.position[1]
                odom.pose.pose.position.z = -msg.position[2]

            # Orientation
            if hasattr(msg, 'q') and len(msg.q) >= 4:
                odom.pose.pose.orientation.w = msg.q[0]
                odom.pose.pose.orientation.x = msg.q[1]
                odom.pose.pose.orientation.y = -msg.q[2]
                odom.pose.pose.orientation.z = -msg.q[3]

            # Velocity (NED to ENU)
            if hasattr(msg, 'velocity') and len(msg.velocity) >= 3:
                odom.twist.twist.linear.x = msg.velocity[0]
                odom.twist.twist.linear.y = -msg.velocity[1]
                odom.twist.twist.linear.z = -msg.velocity[2]

            # Angular velocity
            if hasattr(msg, 'angular_velocity') and len(msg.angular_velocity) >= 3:
                odom.twist.twist.angular.x = msg.angular_velocity[0]
                odom.twist.twist.angular.y = -msg.angular_velocity[1]
                odom.twist.twist.angular.z = -msg.angular_velocity[2]

            getattr(self, f'{drone_name}_odom_pub').publish(odom)
        except Exception as e:
            self.get_logger().error(f"Error in odometry_callback for {drone_name}: {e}")


def main(args=None):
    print('='*60)
    print('PX4 Debug Translator Node')
    print('='*60)
    print('This node translates PX4 messages to standard ROS2 types')
    print('for visualization in RViz2 and debugging.')
    print('')
    print('Topics are published under /debug/<drone_name>/')
    print('where drone_name is "ally" (px4_0) or "enemy" (px4_1)')
    print('='*60)

    rclpy.init(args=args)
    translator = PX4DebugTranslator()

    try:
        rclpy.spin(translator)
    except KeyboardInterrupt:
        translator.get_logger().info('Shutdown requested')
    finally:
        translator.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()