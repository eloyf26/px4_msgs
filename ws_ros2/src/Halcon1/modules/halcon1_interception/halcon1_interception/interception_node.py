import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
import numpy as np
from halcon1_msgs.msg import TrajectoryWithUncertainty, EnemyPose
from px4_msgs.msg import (TrajectorySetpoint, VehicleLocalPosition,
                          OffboardControlMode, VehicleCommand, VehicleStatus)
from halcon1_interception.trajectory_planner import TrajectoryPlanner
from halcon1_interception.px4_command_generator import PX4CommandGenerator

class InterceptionNode(Node):
    def __init__(self):
        super().__init__('interception_node')
        self.get_logger().info('Initializing interception node...')

        # Configure QoS profile for PX4 communication
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        self.get_logger().info('QoS profile configured')

        # Publishers
        self.setpoint_pub = self.create_publisher(
            TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.offboard_control_mode_pub = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.vehicle_command_pub = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', qos_profile)

        # Subscribers
        self.trajectory_sub = self.create_subscription(
            TrajectoryWithUncertainty, '/enemy/predicted_trajectory',
            self.trajectory_callback, 10)
        self.friendly_sub = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position',
            self.friendly_callback, qos_profile)
        self.vehicle_status_sub = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status',
            self.vehicle_status_callback, qos_profile)
        self.enemy_pose_sub = self.create_subscription(
            EnemyPose, '/enemy/pose',
            self.enemy_pose_callback, 10)

        # Algorithms
        self.planner = TrajectoryPlanner()
        self.command_generator = PX4CommandGenerator()

        # 50Hz timer for PX4 commands
        self.get_logger().info('Creating 50Hz timer for PX4 commands...')
        self.command_timer = self.create_timer(0.02, self.publish_setpoint)
        self.get_logger().info('Timer created successfully')

        # State
        self.friendly_position = np.array([0.0, 0.0, 0.0])
        self.friendly_velocity = np.array([0.0, 0.0, 0.0])
        self.enemy_position = np.array([10.0, 5.0, -5.0])  # Default far away
        self.trajectory_start_time = None
        self.interception_enabled = False  # Safety switch
        self.vehicle_status = VehicleStatus()

        # Offboard control state
        self.offboard_setpoint_counter = 0
        self.is_armed = False
        self.offboard_mode_active = False
        self.takeoff_height = -5.0  # 5 meters up (NED frame)
        self.startup_complete = False

        self.get_logger().info('Interception node initialized. Starting offboard control sequence...')

    def friendly_callback(self, msg):
        """Update friendly drone state from PX4"""
        if msg.xy_valid and msg.z_valid:
            self.friendly_position = np.array([msg.x, msg.y, msg.z])
        if msg.v_xy_valid and msg.v_z_valid:
            self.friendly_velocity = np.array([msg.vx, msg.vy, msg.vz])

    def vehicle_status_callback(self, msg):
        """Update vehicle status from PX4"""
        self.vehicle_status = msg
        self.is_armed = msg.arming_state == 2
        self.offboard_mode_active = msg.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD

    def enemy_pose_callback(self, msg):
        """Update enemy drone position"""
        self.enemy_position = np.array([msg.x, msg.y, msg.z])

    def trajectory_callback(self, msg):
        """Process predicted enemy trajectory and plan interception"""
        # Convert message to dict format
        enemy_trajectory = {
            'times': np.array(msg.times),
            'mean': np.column_stack([msg.mean_x, msg.mean_y, msg.mean_z]),
            'upper': np.column_stack([msg.upper_x, msg.upper_y, msg.upper_z]),
            'lower': np.column_stack([msg.lower_x, msg.lower_y, msg.lower_z])
        }

        # Plan interception trajectory
        trajectory = self.planner.plan_interception(
            enemy_trajectory,
            self.friendly_position,
            self.friendly_velocity
        )

        if trajectory is not None:
            self.command_generator.set_trajectory(trajectory)
            # Use ROS2 simulation time
            self.trajectory_start_time = self.get_clock().now()
            self.interception_enabled = True
            self.get_logger().info('New interception trajectory planned')

    def arm(self):
        """Send arm command to vehicle"""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
        self.get_logger().info('Arm command sent')

    def disarm(self):
        """Send disarm command to vehicle"""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=0.0)
        self.get_logger().info('Disarm command sent')

    def engage_offboard_mode(self):
        """Switch to offboard mode"""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0)
        self.get_logger().info('Switching to offboard mode')

    def land(self):
        """Switch to land mode"""
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        self.get_logger().info('Switching to land mode')

    def publish_vehicle_command(self, command, **params):
        """Publish a vehicle command"""
        msg = VehicleCommand()
        msg.command = command
        msg.param1 = params.get("param1", 0.0)
        msg.param2 = params.get("param2", 0.0)
        msg.param3 = params.get("param3", 0.0)
        msg.param4 = params.get("param4", 0.0)
        msg.param5 = params.get("param5", 0.0)
        msg.param6 = params.get("param6", 0.0)
        msg.param7 = params.get("param7", 0.0)
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_pub.publish(msg)

    def publish_offboard_control_mode(self):
        """Publish offboard control mode heartbeat"""
        msg = OffboardControlMode()
        msg.position = True
        msg.velocity = True
        msg.acceleration = True
        msg.attitude = False
        msg.body_rate = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_control_mode_pub.publish(msg)

    def publish_setpoint(self):
        """Publish trajectory setpoint at 50Hz for PX4 offboard control"""
        # Debug: Log first call
        if self.offboard_setpoint_counter == 0:
            self.get_logger().info('First timer callback - starting offboard control')

        # Always publish offboard control mode heartbeat
        self.publish_offboard_control_mode()

        # Handle initial offboard mode activation
        if not self.startup_complete:
            self.offboard_setpoint_counter += 1

            # Send takeoff setpoint before arming
            msg = TrajectorySetpoint()
            msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            msg.position = [0.0, 0.0, self.takeoff_height]
            msg.velocity = [float('nan')] * 3
            msg.acceleration = [float('nan')] * 3
            msg.yaw = 0.0
            msg.yawspeed = float('nan')
            self.setpoint_pub.publish(msg)

            # Log progress
            if self.offboard_setpoint_counter % 10 == 0:
                self.get_logger().info(f'Sending pre-arm setpoints... ({self.offboard_setpoint_counter})')

            # Engage offboard mode and arm after sending some setpoints
            if self.offboard_setpoint_counter == 10:
                self.get_logger().info('Engaging offboard mode and arming...')
                self.engage_offboard_mode()
                self.arm()

            # Mark startup complete after enough setpoints
            if self.offboard_setpoint_counter >= 20:
                self.startup_complete = True
                self.get_logger().info('Startup sequence complete. Drone should be taking off...')
            return

        # Check if we're actually in offboard mode and armed
        if not self.offboard_mode_active or not self.is_armed:
            # Keep trying to arm and engage offboard
            if self.offboard_setpoint_counter % 50 == 0:  # Every second
                self.get_logger().warn(f'Not in offboard mode. Armed: {self.is_armed}, Offboard: {self.offboard_mode_active}')
                if not self.offboard_mode_active:
                    self.engage_offboard_mode()
                if not self.is_armed:
                    self.arm()

            # Keep publishing hover setpoint
            msg = TrajectorySetpoint()
            msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            msg.position = [0.0, 0.0, self.takeoff_height]
            msg.velocity = [float('nan')] * 3
            msg.acceleration = [float('nan')] * 3
            msg.yaw = 0.0
            msg.yawspeed = float('nan')
            self.setpoint_pub.publish(msg)
            self.offboard_setpoint_counter += 1
            return

        # Check if still taking off
        if self.friendly_position[2] > self.takeoff_height + 1.0:
            # Still ascending to takeoff height
            msg = TrajectorySetpoint()
            msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            msg.position = [0.0, 0.0, self.takeoff_height]
            msg.velocity = [float('nan')] * 3
            msg.acceleration = [float('nan')] * 3
            msg.yaw = 0.0
            msg.yawspeed = float('nan')
            self.setpoint_pub.publish(msg)

            if self.offboard_setpoint_counter % 50 == 0:  # Log every second
                self.get_logger().info(f'Taking off... Current altitude: {-self.friendly_position[2]:.1f}m, Target: {-self.takeoff_height:.1f}m')
            self.offboard_setpoint_counter += 1
            return

        # Check if we have an interception trajectory
        if not self.interception_enabled or self.trajectory_start_time is None:
            # Hover at current position
            msg = TrajectorySetpoint()
            msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            msg.position = self.friendly_position.tolist()
            msg.velocity = [float('nan')] * 3
            msg.acceleration = [float('nan')] * 3
            msg.yaw = 0.0
            msg.yawspeed = float('nan')
            self.setpoint_pub.publish(msg)

            # Log status periodically
            if self.offboard_setpoint_counter % 100 == 0:  # Every 2 seconds
                distance_to_enemy = np.linalg.norm(self.friendly_position - self.enemy_position)
                self.get_logger().info(f'Hovering at {-self.friendly_position[2]:.1f}m altitude. Enemy distance: {distance_to_enemy:.1f}m. Waiting for interception trajectory...')
            self.offboard_setpoint_counter += 1
            return

        # Get current time in trajectory using ROS2 time
        time_diff = self.get_clock().now() - self.trajectory_start_time
        current_time = time_diff.nanoseconds / 1e9  # Convert to seconds

        # Get setpoint from generator
        setpoint = self.command_generator.get_setpoint(current_time)

        if setpoint is None:
            self.interception_enabled = False
            return

        # Create PX4 TrajectorySetpoint message
        msg = TrajectorySetpoint()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        msg.position = setpoint['position']
        msg.velocity = setpoint['velocity']
        msg.acceleration = setpoint['acceleration']
        msg.yaw = setpoint['yaw']
        msg.yawspeed = setpoint['yawspeed']
        self.setpoint_pub.publish(msg)

        # Check distance to enemy drone (interception success)
        distance_to_enemy = np.linalg.norm(self.friendly_position - self.enemy_position)

        if distance_to_enemy < 0.5:  # Within 0.5 meters of enemy
            self.get_logger().info('🎯 INTERCEPTION SUCCESSFUL! Enemy drone intercepted within 0.5m')
            self.get_logger().info(f'Final distance: {distance_to_enemy:.2f}m')
            self.land()
            self.interception_enabled = False
            return

        # Check if trajectory is complete
        if self.command_generator.is_trajectory_complete(current_time):
            self.interception_enabled = False
            self.get_logger().info('Interception trajectory complete - target not intercepted')
            self.land()

def main():
    rclpy.init()
    node = InterceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()