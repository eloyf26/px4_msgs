import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
import numpy as np
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from px4_msgs.msg import TrajectorySetpoint, VehicleOdometry, OffboardControlMode
from halcon1_interception.trajectory_planner import TrajectoryPlanner, TrajectoryPlannerParameters
from halcon1_interception.px4_command_generator import PX4CommandGenerator, InterceptionTrajectory
from halcon1_types import DronePose, TimestampedTrajectory

OFFBOARD_MSG = OffboardControlMode()
OFFBOARD_MSG.position = True
OFFBOARD_MSG.velocity = False
OFFBOARD_MSG.acceleration = False
OFFBOARD_MSG.attitude = False
OFFBOARD_MSG.body_rate = False

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
        self.debug_trajectory_pub = self.create_publisher(
            Path, '/debug/interception_trajectory', 10)

        # Subscribers
        self.trajectory_sub = self.create_subscription(
            Path, '/enemy/trajectory_prediction',
            self.trajectory_callback, 10)
        self.friendly_sub = self.create_subscription(
            VehicleOdometry, '/fmu/out/vehicle_odometry',
            self.friendly_callback, qos_profile)

        # Algorithms
        self.planner = TrajectoryPlanner(TrajectoryPlannerParameters())

        # State
        self.friendly_pose = None
        self.current_interception_trajectory = None

        # Timer for 50Hz publishing
        self.timer = self.create_timer(0.02, self.publish_command)

        self.get_logger().info('Interception node ready. Arm and takeoff manually via QGroundControl.')
        self.get_logger().info('Once airborne, the system will automatically intercept detected enemies.')

    def friendly_callback(self, msg):
        """Update friendly drone pose from PX4 odometry"""
        self.friendly_pose = DronePose(
            x=msg.position[0],
            y=msg.position[1],
            z=msg.position[2]
        )

    def trajectory_callback(self, msg):
        """Process predicted trajectory and plan interception"""
        if self.friendly_pose is None:
            self.get_logger().warn_throttle(5.0, 'No friendly pose available for interception planning')
            return

        # Only process if we have valid trajectory data
        if len(msg.poses) == 0:
            return

        # Convert NavPath to TimestampedTrajectory
        timestamps = []
        positions = []

        for pose_stamped in msg.poses:
            timestamp = pose_stamped.header.stamp.sec + pose_stamped.header.stamp.nanosec * 1e-9
            position = DronePose(
                x=pose_stamped.pose.position.x,
                y=pose_stamped.pose.position.y,
                z=pose_stamped.pose.position.z
            )
            timestamps.append(timestamp)
            positions.append(position)

        enemy_trajectory = TimestampedTrajectory(timestamps, positions)

        # Plan interception
        interception_trajectory = self.planner.plan_interception(enemy_trajectory, self.friendly_pose)

        # Publish debug trajectory for visualization
        self.publish_debug_trajectory(interception_trajectory)

        # Generate interception trajectory with PX4 setpoints
        current_time = self.get_clock().now().nanoseconds / 1e9
        self.current_interception_trajectory = PX4CommandGenerator.generate_interception_trajectory(
            interception_trajectory, current_time)

    def publish_debug_trajectory(self, trajectory: TimestampedTrajectory):
        """Publish interception trajectory for visualization"""
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = 'world'

        for timestamp, position in zip(trajectory.timestamps, trajectory.positions):
            pose_stamped = PoseStamped()
            pose_stamped.header.stamp.sec = int(timestamp)
            pose_stamped.header.stamp.nanosec = int((timestamp - int(timestamp)) * 1e9)
            pose_stamped.header.frame_id = 'world'

            pose_stamped.pose.position.x = position.x
            pose_stamped.pose.position.y = position.y
            pose_stamped.pose.position.z = position.z

            pose_stamped.pose.orientation.w = 1.0

            path_msg.poses.append(pose_stamped)

        self.debug_trajectory_pub.publish(path_msg)

    def publish_command(self):
        """Publish commands at 50Hz"""
        # Always publish offboard control mode
        OFFBOARD_MSG.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_mode_pub.publish(OFFBOARD_MSG)

        # Generate and publish trajectory setpoint
        if self.friendly_pose is None:
            return

        current_time = self.get_clock().now().nanoseconds / 1e9

        if (self.current_interception_trajectory is not None and
            self.current_interception_trajectory.is_active and
            not PX4CommandGenerator.is_trajectory_complete(self.current_interception_trajectory, current_time)):

            # Generate current setpoint from interception trajectory
            setpoint = PX4CommandGenerator.generate_current_setpoint(
                self.current_interception_trajectory, current_time, self.friendly_pose)
        else:
            # No active trajectory - hover at current position
            setpoint = TrajectorySetpoint()
            setpoint.timestamp = int(current_time * 1e6)
            setpoint.position = [float(self.friendly_pose.x), float(self.friendly_pose.y), float(self.friendly_pose.z)]
            setpoint.velocity = [float('nan')] * 3
            setpoint.acceleration = [float('nan')] * 3
            setpoint.yaw = float('nan')
            setpoint.yawspeed = float('nan')

        self.setpoint_pub.publish(setpoint)

def main():
    rclpy.init()
    node = InterceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()