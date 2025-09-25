#!/usr/bin/env python3

import math
import time
import random
import sys
import select
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition


class EnemyOffboardControl(Node):
    """Node for controlling the enemy drone movement patterns in offboard mode."""

    def __init__(self) -> None:
        super().__init__('enemy_offboard_control')

        # Declare parameters
        self.declare_parameter('pattern', 'circle')  # circle, figure8, random
        self.declare_parameter('duration', 0.0)  # 0 means non-stop

        # Get parameters
        self.pattern = self.get_parameter('pattern').value
        self.duration = self.get_parameter('duration').value

        # Validate pattern
        valid_patterns = ['circle', 'figure8', 'random']
        if self.pattern not in valid_patterns:
            self.get_logger().error(f"Invalid pattern: {self.pattern}. Using 'circle'.")
            self.pattern = 'circle'

        self.get_logger().info(f"Enemy drone pattern: {self.pattern}, Duration: {self.duration}s (0=infinite)")

        # Configure QoS profile
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=0
        )

        # Create publishers for enemy drone (instance 1 - px4_1 namespace)
        self.offboard_control_mode_publisher = self.create_publisher(
            OffboardControlMode, '/px4_1/fmu/in/offboard_control_mode', qos_profile)
        self.trajectory_setpoint_publisher = self.create_publisher(
            TrajectorySetpoint, '/px4_1/fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_publisher = self.create_publisher(
            VehicleCommand, '/px4_1/fmu/in/vehicle_command', qos_profile)

        # Create subscriber to get current position
        self.vehicle_local_position_subscriber = self.create_subscription(
            VehicleLocalPosition, '/px4_1/fmu/out/vehicle_local_position_v1',
            self.vehicle_local_position_callback, qos_profile)

        # Movement parameters
        self.start_time = time.time()
        self.pattern_started = False
        self.offboard_counter = 0
        self.current_altitude = -5.0  # Default altitude (will be updated from actual position)
        self.vehicle_local_position = None

        # Pattern-specific parameters
        self.circle_radius = 50.0  # meters
        self.circle_speed = 1.0  # rad/s
        self.figure8_size = 50.0  # meters
        self.figure8_speed = 0.5  # rad/s
        self.random_speed = 2.0  # m/s
        self.random_bounds = 100.0  # meters
        self.random_target = None
        self.random_target_time = 0

        # Create a timer to publish at 10Hz (required for offboard mode)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info('Enemy offboard control node initialized')

    def vehicle_local_position_callback(self, msg):
        """Callback function for vehicle_local_position topic subscriber."""
        self.vehicle_local_position = msg
        if self.current_altitude == -5.0:  # Only update once on first callback
            self.current_altitude = msg.z

    def publish_offboard_control_mode(self):
        """Publish the offboard control mode."""
        msg = OffboardControlMode()
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_control_mode_publisher.publish(msg)

    def publish_position_setpoint(self, x: float, y: float, z: float):
        """Publish the trajectory setpoint."""
        msg = TrajectorySetpoint()
        msg.position = [x, y, z]
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.trajectory_setpoint_publisher.publish(msg)

    def engage_offboard_mode(self):
        """Switch to offboard mode."""
        msg = VehicleCommand()
        msg.command = VehicleCommand.VEHICLE_CMD_DO_SET_MODE
        msg.param1 = 1.0  # Custom mode
        msg.param2 = 6.0  # Offboard
        msg.target_system = 2  # Instance 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher.publish(msg)
        self.get_logger().info("Switching to offboard mode")

    def land(self):
        """Switch to land mode."""
        msg = VehicleCommand()
        msg.command = VehicleCommand.VEHICLE_CMD_NAV_LAND
        msg.target_system = 2  # Instance 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher.publish(msg)
        self.get_logger().info("Landing...")

    def get_circle_position(self, t: float):
        """Calculate position for circular pattern."""
        angle = self.circle_speed * t
        x = self.circle_radius * math.cos(angle)
        y = -2.0 + self.circle_radius * math.sin(angle)
        z = self.current_altitude
        return x, y, z

    def get_figure8_position(self, t: float):
        """Calculate position for figure-8 pattern (horizontal infinity symbol)."""
        # Parametric equations for a horizontal figure-8 (lemniscate)
        angle = self.figure8_speed * t
        # Scale factor for the figure-8
        scale = self.figure8_size / 2

        # Lemniscate parametric equations
        # x = a * cos(t) / (1 + sin²(t))
        # y = a * sin(t) * cos(t) / (1 + sin²(t))
        denominator = 1 + math.sin(angle) ** 2
        x = scale * 2 * math.cos(angle) / denominator
        y = -2.0 + scale * 2 * math.sin(angle) * math.cos(angle) / denominator
        z = self.current_altitude
        return x, y, z

    def get_random_position(self, t: float):
        """Calculate position for random movement pattern."""
        # Generate new random target every 5 seconds
        if self.random_target is None or t - self.random_target_time > 5.0:
            self.random_target = (
                random.uniform(-self.random_bounds/2, self.random_bounds/2),
                -2.0 + random.uniform(-self.random_bounds/2, self.random_bounds/2),
                self.current_altitude
            )
            self.random_target_time = t
            self.get_logger().info(f"New random target: ({self.random_target[0]:.1f}, {self.random_target[1]:.1f})")

        return self.random_target

    def timer_callback(self) -> None:
        """Callback function for the timer."""
        # Always publish offboard control mode (required by PX4)
        self.publish_offboard_control_mode()

        # Send initial offboard commands
        if self.offboard_counter < 10:
            self.offboard_counter += 1
            if self.offboard_counter == 10:
                self.engage_offboard_mode()
                self.pattern_started = True
                self.start_time = time.time()
                self.get_logger().info("Starting movement pattern...")

        # Check if duration has expired
        if self.duration > 0:
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration:
                self.land()
                self.timer.cancel()
                self.get_logger().info(f"Duration of {self.duration}s completed. Landing.")
                return

        # Calculate position based on pattern
        t = time.time() - self.start_time

        if self.pattern == 'circle':
            x, y, z = self.get_circle_position(t)
        elif self.pattern == 'figure8':
            x, y, z = self.get_figure8_position(t)
        elif self.pattern == 'random':
            x, y, z = self.get_random_position(t)
        else:
            # Default: hover at current position
            return

        # Publish position setpoint (maintain current altitude)
        self.publish_position_setpoint(x, y, z)


def get_user_input():
    """Get movement pattern and duration from user interactively."""
    print('\n=========================================')
    print('   ENEMY DRONE MOVEMENT CONTROL')
    print('=========================================')
    print()
    print('Select movement pattern:')
    print('  1 - Circular movement')
    print('  2 - Figure-8 movement')
    print('  3 - Random movement')
    print()
    print('Press 1, 2, or 3 (or any other key for default circular):')

    # Get pattern selection with timeout
    pattern_input = input().strip()

    pattern_map = {
        '1': 'circle',
        '2': 'figure8',
        '3': 'random'
    }

    pattern = pattern_map.get(pattern_input, 'circle')

    if pattern_input not in pattern_map:
        print(f'Invalid selection "{pattern_input}". Using default: circular movement')
    else:
        print(f'Selected: {pattern} movement')

    print()
    print('Enter duration in seconds (or press ENTER for infinite):')
    duration_input = input().strip()

    try:
        duration = float(duration_input) if duration_input else 0.0
        if duration > 0:
            print(f'Duration: {duration} seconds')
        else:
            print('Duration: Infinite')
    except ValueError:
        print('Invalid duration. Using infinite duration.')
        duration = 0.0

    print()
    print('=========================================')
    print(f'Starting {pattern} movement for {duration}s (0=infinite)...')
    print('=========================================')
    print()

    return pattern, duration


def main(args=None) -> None:
    # Get user input for movement pattern and duration
    pattern, duration = get_user_input()

    # Override command line args with user selection
    modified_args = []
    if args:
        # Filter out existing pattern and duration args
        for arg in args:
            if not arg.startswith('-p pattern:=') and not arg.startswith('-p duration:='):
                modified_args.append(arg)

    # Add selected pattern and duration
    modified_args.extend([
        '--ros-args',
        f'-p', f'pattern:={pattern}',
        f'-p', f'duration:={duration}'
    ])

    rclpy.init(args=modified_args)
    enemy_offboard_control = EnemyOffboardControl()

    try:
        rclpy.spin(enemy_offboard_control)
    except KeyboardInterrupt:
        enemy_offboard_control.get_logger().info('Interrupted by user')
    finally:
        enemy_offboard_control.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")