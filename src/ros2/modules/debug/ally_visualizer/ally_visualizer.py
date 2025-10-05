#!/usr/bin/env python3
"""
Ally Drone Visualizer for RViz2

Translates ally PX4 messages from /fmu/out/ topics to standard ROS2 debug topics.
This visualizer is simulator-agnostic - works with Gazebo, AirSim, Isaac Sim, etc.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import TrajectorySetpoint, VehicleOdometry
from geometry_msgs.msg import PoseStamped, TwistStamped
from nav_msgs.msg import Path, Odometry
from std_msgs.msg import String, Int32
from transforms import CoordinateTransform
import math


class AllyVisualizer(Node):
    """Translates ally PX4 messages to RViz2-compatible debug topics."""

    def __init__(self):
        super().__init__('ally_visualizer')

        self.get_logger().info('Ally Visualizer starting...')

        # Configure QoS profile for PX4 topics
        self.px4_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=0
        )

        # Standard QoS for ROS2 debug topics
        self.ros_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Initialize path tracking
        self.path = Path()
        self.path.header.frame_id = 'world'
        self.max_path_length = 1000

        # Subscribers to ally PX4 topics (no namespace)
        self.create_subscription(
            VehicleOdometry,
            '/fmu/out/vehicle_odometry',
            self.odometry_callback,
            self.px4_qos
        )

        self.create_subscription(
            TrajectorySetpoint,
            '/fmu/in/trajectory_setpoint',
            self.setpoint_callback,
            self.px4_qos
        )

        # Publishers for ally debug topics
        self.pose_pub = self.create_publisher(
            PoseStamped, '/debug/ally/pose', self.ros_qos)

        self.velocity_pub = self.create_publisher(
            TwistStamped, '/debug/ally/velocity', self.ros_qos)

        self.setpoint_pub = self.create_publisher(
            PoseStamped, '/debug/ally/setpoint', self.ros_qos)

        self.path_pub = self.create_publisher(
            Path, '/debug/ally/path', self.ros_qos)

        self.odom_pub = self.create_publisher(
            Odometry, '/debug/ally/odometry', self.ros_qos)

        self.get_logger().info('Ally Visualizer initialized')
        self.get_logger().info('Publishing debug topics:')
        self.get_logger().info('  - /debug/ally/pose (PoseStamped)')
        self.get_logger().info('  - /debug/ally/velocity (TwistStamped)')
        self.get_logger().info('  - /debug/ally/setpoint (PoseStamped)')
        self.get_logger().info('  - /debug/ally/path (Path)')
        self.get_logger().info('  - /debug/ally/odometry (Odometry)')

    def setpoint_callback(self, msg):
        """Convert TrajectorySetpoint to PoseStamped for visualization."""
        try:
            pose = PoseStamped()
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.header.frame_id = 'world'

            # Transform position from NED to ENU
            if hasattr(msg, 'position') and len(msg.position) >= 3:
                ned_pos = [
                    float(msg.position[0]) if not math.isnan(msg.position[0]) else 0.0,
                    float(msg.position[1]) if not math.isnan(msg.position[1]) else 0.0,
                    float(msg.position[2]) if not math.isnan(msg.position[2]) else 0.0
                ]
                enu_pos = CoordinateTransform.ned_to_enu_local_frame(ned_pos)
                pose.pose.position.x = enu_pos.x
                pose.pose.position.y = enu_pos.y
                pose.pose.position.z = enu_pos.z

            # Default orientation
            pose.pose.orientation.w = 1.0
            pose.pose.orientation.x = 0.0
            pose.pose.orientation.y = 0.0
            pose.pose.orientation.z = 0.0

            self.setpoint_pub.publish(pose)

        except Exception as e:
            self.get_logger().error(f"Error in setpoint_callback: {e}")

    def odometry_callback(self, msg):
        """Convert VehicleOdometry to ROS2 Odometry and PoseStamped."""
        try:
            timestamp = self.get_clock().now().to_msg()

            # Create Odometry message
            odom = Odometry()
            odom.header.stamp = timestamp
            odom.header.frame_id = 'world'
            odom.child_frame_id = 'ally_base_link'

            # Transform position from NED to ENU
            if hasattr(msg, 'position') and len(msg.position) >= 3:
                enu_pos = CoordinateTransform.ned_to_enu_local_frame(msg.position)
                odom.pose.pose.position.x = float(enu_pos.x)
                odom.pose.pose.position.y = float(enu_pos.y)
                odom.pose.pose.position.z = float(enu_pos.z)

            # Transform orientation from PX4 (FRD-to-NED) to ROS2 (FLU-to-ENU)
            if hasattr(msg, 'q') and len(msg.q) >= 4:
                # Reorder PX4 quaternion from [w,x,y,z] to [x,y,z,w]
                q_px4_wxyz = list(msg.q)
                q_px4_xyzw = [q_px4_wxyz[1], q_px4_wxyz[2], q_px4_wxyz[3], q_px4_wxyz[0]]

                enu_quat = CoordinateTransform.px4_to_ros_orientation(q_px4_xyzw)
                odom.pose.pose.orientation.x = float(enu_quat[0])
                odom.pose.pose.orientation.y = float(enu_quat[1])
                odom.pose.pose.orientation.z = float(enu_quat[2])
                odom.pose.pose.orientation.w = float(enu_quat[3])

            # Transform velocity from NED to ENU
            if hasattr(msg, 'velocity') and len(msg.velocity) >= 3:
                enu_vel = CoordinateTransform.ned_to_enu_local_frame(msg.velocity)
                odom.twist.twist.linear.x = float(enu_vel.x)
                odom.twist.twist.linear.y = float(enu_vel.y)
                odom.twist.twist.linear.z = float(enu_vel.z)

            # Transform angular velocity from NED to ENU
            if hasattr(msg, 'angular_velocity') and len(msg.angular_velocity) >= 3:
                enu_ang_vel = CoordinateTransform.ned_to_enu_local_frame(msg.angular_velocity)
                odom.twist.twist.angular.x = float(enu_ang_vel.x)
                odom.twist.twist.angular.y = float(enu_ang_vel.y)
                odom.twist.twist.angular.z = float(enu_ang_vel.z)

            self.odom_pub.publish(odom)

            # Publish as PoseStamped for easier visualization
            pose = PoseStamped()
            pose.header = odom.header
            pose.pose = odom.pose.pose
            self.pose_pub.publish(pose)

            # Publish velocity as TwistStamped
            velocity = TwistStamped()
            velocity.header = odom.header
            velocity.twist = odom.twist.twist
            self.velocity_pub.publish(velocity)

            # Update and publish path
            self.path.header.stamp = timestamp
            self.path.poses.append(pose)

            # Limit path length
            if len(self.path.poses) > self.max_path_length:
                self.path.poses.pop(0)

            self.path_pub.publish(self.path)

        except Exception as e:
            self.get_logger().error(f"Error in odometry_callback: {e}")


def main(args=None):
    print('='*60)
    print('Ally Visualizer Node')
    print('='*60)
    print('Translates ally PX4 odometry to RViz2 debug topics')
    print('Publishes to /debug/ally/*')
    print('='*60)

    rclpy.init(args=args)
    visualizer = AllyVisualizer()

    try:
        rclpy.spin(visualizer)
    except KeyboardInterrupt:
        visualizer.get_logger().info('Shutdown requested')
    finally:
        visualizer.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
