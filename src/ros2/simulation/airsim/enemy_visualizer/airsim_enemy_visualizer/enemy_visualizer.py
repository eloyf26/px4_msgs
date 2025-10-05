#!/usr/bin/env python3
"""
Enemy Drone Visualizer for AirSim

Queries AirSim API for enemy ground truth position and publishes to ROS2 debug topics.
Uses simGetObjectPose() which returns global AirSim positions.
Subtracts ally offset to convert to PX4 local frame (origin at ally spawn).
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from geometry_msgs.msg import PoseStamped, TwistStamped, Point
from nav_msgs.msg import Path, Odometry
from transforms import CoordinateTransform
import math

try:
    import airsim
    AIRSIM_AVAILABLE = True
except ImportError:
    AIRSIM_AVAILABLE = False


class EnemyVisualizerAirSim(Node):
    """Translates enemy position from AirSim API to RViz2-compatible debug topics."""

    def __init__(self):
        super().__init__('enemy_visualizer')

        if not AIRSIM_AVAILABLE:
            self.get_logger().error('AirSim Python package not found. Install with: pip install airsim')
            raise ImportError('airsim package required')

        self.get_logger().info('Enemy Visualizer (AirSim) starting...')

        # Standard QoS for ROS2 debug topics
        self.ros_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Declare parameters for ally spawn position (to convert from AirSim global to PX4 local frame)
        self.declare_parameter('ally_offset_x', 0.0)
        self.declare_parameter('ally_offset_y', 0.0)
        self.declare_parameter('ally_offset_z', 0.0)
        self.declare_parameter('host_ip', 'localhost')
        self.declare_parameter('update_rate', 30.0)  # Hz

        # Get parameters
        ally_offset_x = self.get_parameter('ally_offset_x').value
        ally_offset_y = self.get_parameter('ally_offset_y').value
        ally_offset_z = self.get_parameter('ally_offset_z').value
        host_ip = self.get_parameter('host_ip').value
        update_rate = self.get_parameter('update_rate').value

        self.get_logger().info(f'Ally offset position: x={ally_offset_x}, y={ally_offset_y}, z={ally_offset_z}')

        # Store ally offset in NED (AirSim coordinate system)
        # simGetObjectPose returns global AirSim positions, we subtract ally offset to get PX4 local frame
        # AirSim uses NED: X=North, Y=East, Z=Down
        self.ally_offset_ned = [
            ally_offset_x,  # North
            ally_offset_y,  # East
            ally_offset_z   # Down (positive down)
        ]

        # Connect to AirSim
        self.get_logger().info(f'Connecting to AirSim at {host_ip}...')
        try:
            self.airsim_client = airsim.MultirotorClient(ip=host_ip)
            self.airsim_client.confirmConnection()
            self.get_logger().info('✓ Connected to AirSim')
        except Exception as e:
            self.get_logger().error(f'Failed to connect to AirSim: {e}')
            raise

        # Initialize path tracking
        self.path = Path()
        self.path.header.frame_id = 'world'
        self.max_path_length = 1000

        # Publishers for enemy debug topics
        self.pose_pub = self.create_publisher(
            PoseStamped, '/debug/enemy/pose', self.ros_qos)

        self.velocity_pub = self.create_publisher(
            TwistStamped, '/debug/enemy/velocity', self.ros_qos)

        self.path_pub = self.create_publisher(
            Path, '/debug/enemy/path', self.ros_qos)

        self.odom_pub = self.create_publisher(
            Odometry, '/debug/enemy/odometry', self.ros_qos)

        # Create timer to query AirSim at specified rate
        timer_period = 1.0 / update_rate
        self.timer = self.create_timer(timer_period, self.update_enemy_state)

        self.get_logger().info('Enemy Visualizer (AirSim) initialized')
        self.get_logger().info(f'Update rate: {update_rate} Hz')
        self.get_logger().info('Publishing debug topics:')
        self.get_logger().info('  - /debug/enemy/pose (PoseStamped)')
        self.get_logger().info('  - /debug/enemy/velocity (TwistStamped)')
        self.get_logger().info('  - /debug/enemy/path (Path)')
        self.get_logger().info('  - /debug/enemy/odometry (Odometry)')

    def update_enemy_state(self):
        """Query AirSim for enemy state and publish to ROS2 topics."""
        try:
            timestamp = self.get_clock().now().to_msg()

            # Get Enemy pose from AirSim scene (use simGetObjectPose instead of getMultirotorState)
            # simGetObjectPose returns the actual scene/visual position, which is correct even before physics init
            # getMultirotorState returns physics position, which can cause "Exception occurred while updating world"
            enemy_pose = self.airsim_client.simGetObjectPose("Enemy")

            # AirSim uses NED coordinates
            # Enemy position is in AirSim global NED frame
            # PX4 local frame origin is at Ally's spawn position
            # So we need to subtract Ally's spawn offset to get position relative to PX4 origin
            ned_pos = enemy_pose.position
            enemy_pos_airsim_ned = [ned_pos.x_val, ned_pos.y_val, ned_pos.z_val]

            # Subtract Ally spawn offset to get position in PX4 local frame
            enemy_pos_px4_ned = [
                enemy_pos_airsim_ned[0] - self.ally_offset_ned[0],
                enemy_pos_airsim_ned[1] - self.ally_offset_ned[1],
                enemy_pos_airsim_ned[2] - self.ally_offset_ned[2]
            ]

            # Convert NED to ENU for ROS2
            enu_pos = CoordinateTransform.ned_to_enu_local_frame(enemy_pos_px4_ned)

            # Create Odometry message
            odom = Odometry()
            odom.header.stamp = timestamp
            odom.header.frame_id = 'world'
            odom.child_frame_id = 'enemy_base_link'

            # Position
            odom.pose.pose.position.x = float(enu_pos.x)
            odom.pose.pose.position.y = float(enu_pos.y)
            odom.pose.pose.position.z = float(enu_pos.z)

            # Orientation (convert AirSim quaternion to ROS2)
            # AirSim quaternion is in NED frame
            q_airsim = enemy_pose.orientation
            q_ned = [q_airsim.x_val, q_airsim.y_val, q_airsim.z_val, q_airsim.w_val]

            # Convert NED orientation to ENU
            enu_quat = CoordinateTransform.px4_to_ros_orientation(q_ned)
            odom.pose.pose.orientation.x = float(enu_quat[0])
            odom.pose.pose.orientation.y = float(enu_quat[1])
            odom.pose.pose.orientation.z = float(enu_quat[2])
            odom.pose.pose.orientation.w = float(enu_quat[3])

            # Velocity - get from getMultirotorState for kinematic data
            enemy_state = self.airsim_client.getMultirotorState(vehicle_name="Enemy")
            kinematics = enemy_state.kinematics_estimated

            # Velocity (convert NED to ENU)
            vel_ned = [
                kinematics.linear_velocity.x_val,
                kinematics.linear_velocity.y_val,
                kinematics.linear_velocity.z_val
            ]
            enu_vel = CoordinateTransform.ned_to_enu_local_frame(vel_ned)
            odom.twist.twist.linear.x = float(enu_vel.x)
            odom.twist.twist.linear.y = float(enu_vel.y)
            odom.twist.twist.linear.z = float(enu_vel.z)

            # Angular velocity (convert NED to ENU)
            ang_vel_ned = [
                kinematics.angular_velocity.x_val,
                kinematics.angular_velocity.y_val,
                kinematics.angular_velocity.z_val
            ]
            enu_ang_vel = CoordinateTransform.ned_to_enu_local_frame(ang_vel_ned)
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
            self.get_logger().error(f"Error querying AirSim: {e}")


def main(args=None):
    print('='*60)
    print('Enemy Visualizer Node (AirSim)')
    print('='*60)
    print('Queries AirSim API for enemy ground truth position')
    print('Subtracts ally offset from global position')
    print('Publishes to /debug/enemy/*')
    print('='*60)

    rclpy.init(args=args)

    try:
        visualizer = EnemyVisualizerAirSim()
        rclpy.spin(visualizer)
    except KeyboardInterrupt:
        print('Shutdown requested')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        try:
            visualizer.destroy_node()
        except:
            pass
        rclpy.shutdown()


if __name__ == '__main__':
    main()
