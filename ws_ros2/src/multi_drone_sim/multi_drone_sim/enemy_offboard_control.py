#!/usr/bin/env python3

import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition, VehicleStatus


class EnemyOffboardControl(Node):
    """Node for controlling the enemy drone in offboard mode."""

    def __init__(self) -> None:
        super().__init__('enemy_offboard_control')

        # Configure QoS profile - depth MUST be 0
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

        # Create subscribers
        self.vehicle_local_position_subscriber = self.create_subscription(
            VehicleLocalPosition, '/px4_1/fmu/out/vehicle_local_position_v1',
            self.vehicle_local_position_callback, qos_profile)
        self.vehicle_status_subscriber = self.create_subscription(
            VehicleStatus, '/px4_1/fmu/out/vehicle_status_v1',
            self.vehicle_status_callback, qos_profile)

        # Initialize variables
        self.offboard_setpoint_counter = 0
        self.vehicle_local_position = VehicleLocalPosition()
        self.vehicle_status = VehicleStatus()
        self.takeoff_height = -5.0  # 5 meters altitude (NED frame)

        # Flight control variables
        self.flight_phase = "INIT"  # INIT, ARMED, TAKEOFF, BACKWARD, LAND, DONE
        self.start_backward_time = None
        self.backward_duration = 10.0  # 10 seconds
        self.backward_velocity = -2.0  # m/s backward
        self.initial_x_position = None

        # Create a timer to publish at 10Hz (required for offboard mode)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info('Enemy offboard control node initialized')

    def vehicle_local_position_callback(self, msg):
        """Callback function for vehicle_local_position topic subscriber."""
        self.vehicle_local_position = msg

    def vehicle_status_callback(self, msg):
        """Callback function for vehicle_status topic subscriber."""
        # Log any status changes for debugging
        if msg.nav_state != self.vehicle_status.nav_state:
            nav_states = {
                0: "MANUAL", 1: "ALTCTL", 2: "POSCTL", 3: "AUTO_MISSION",
                4: "AUTO_LOITER", 5: "AUTO_RTL", 14: "OFFBOARD",
                7: "STAB", 8: "AUTO_TAKEOFF", 9: "AUTO_LAND", 10: "AUTO_FOLLOW_TARGET",
                11: "AUTO_PRECISION_LAND", 12: "ORBIT", 13: "AUTO_VTOL_TAKEOFF"
            }
            old_nav = nav_states.get(self.vehicle_status.nav_state, f"UNKNOWN({self.vehicle_status.nav_state})")
            new_nav = nav_states.get(msg.nav_state, f"UNKNOWN({msg.nav_state})")
            self.get_logger().info(f"NAV STATE CHANGED: {old_nav} -> {new_nav}")

        if msg.arming_state != self.vehicle_status.arming_state:
            arm_states = {
                0: "INIT", 1: "STANDBY", 2: "ARMED",
                3: "STANDBY_ERROR", 4: "SHUTDOWN", 5: "IN_AIR_RESTORE"
            }
            old_arm = arm_states.get(self.vehicle_status.arming_state, f"UNKNOWN({self.vehicle_status.arming_state})")
            new_arm = arm_states.get(msg.arming_state, f"UNKNOWN({msg.arming_state})")
            self.get_logger().info(f"ARMING STATE CHANGED: {old_arm} -> {new_arm}")

        self.vehicle_status = msg

    def arm(self):
        """Send an arm command to the vehicle."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
        self.get_logger().info('Arm command sent')

    def disarm(self):
        """Send a disarm command to the vehicle."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=0.0)
        self.get_logger().info('Disarm command sent')

    def engage_offboard_mode(self):
        """Switch to offboard mode."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1=1.0,
            param2=6.0)
        self.get_logger().info("Switching to offboard mode")

    def land(self):
        """Switch to land mode."""
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        self.get_logger().info("Switching to land mode")

    def publish_offboard_control_heartbeat_signal(self):
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

    def publish_vehicle_command(self, command, **params) -> None:
        """Publish a vehicle command."""
        msg = VehicleCommand()
        msg.command = command
        msg.param1 = params.get("param1", 0.0)
        msg.param2 = params.get("param2", 0.0)
        msg.param3 = params.get("param3", 0.0)
        msg.param4 = params.get("param4", 0.0)
        msg.param5 = params.get("param5", 0.0)
        msg.param6 = params.get("param6", 0.0)
        msg.param7 = params.get("param7", 0.0)
        # CRITICAL: For instance 1, target_system must be 2
        msg.target_system = 2
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher.publish(msg)
        self.get_logger().debug(f"Published command {command} with target_system={msg.target_system}, param1={msg.param1}, param2={msg.param2}")

    def timer_callback(self) -> None:
        """Callback function for the timer."""
        # CRITICAL: Always publish offboard control mode and position setpoints
        # PX4 requires continuous streaming at >2Hz
        self.publish_offboard_control_heartbeat_signal()

        # Always publish a position setpoint
        if self.flight_phase == "INIT":
            self.publish_position_setpoint(0.0, -2.0, -5.0)
        elif self.flight_phase == "ARMED":
            self.publish_position_setpoint(0.0, -2.0, -5.0)
        elif self.flight_phase == "TAKEOFF":
            self.publish_position_setpoint(self.initial_x_position, -2.0, self.takeoff_height)
        elif self.flight_phase == "BACKWARD":
            elapsed = time.time() - self.start_backward_time
            backward_distance = self.backward_velocity * elapsed
            target_x = self.initial_x_position + backward_distance
            self.publish_position_setpoint(target_x, -2.0, self.takeoff_height)
        else:  # LAND or DONE
            self.publish_position_setpoint(
                self.vehicle_local_position.x,
                self.vehicle_local_position.y,
                self.vehicle_local_position.z)

        # Wait for some offboard heartbeats before trying to arm
        if self.offboard_setpoint_counter < 10:
            self.offboard_setpoint_counter += 1
            return

        # Arm and switch to offboard
        if self.offboard_setpoint_counter == 10:
            self.get_logger().info("Sending arm and offboard commands...")
            self.get_logger().info(f"Current state - Nav: {self.vehicle_status.nav_state}, Arm: {self.vehicle_status.arming_state}")
            self.arm()
            self.engage_offboard_mode()
            self.offboard_setpoint_counter += 1
            self.flight_phase = "ARMED"
            return

        # Check if we're armed and in offboard mode
        if (self.vehicle_status.nav_state != VehicleStatus.NAVIGATION_STATE_OFFBOARD or
            self.vehicle_status.arming_state != VehicleStatus.ARMING_STATE_ARMED):
            # Log periodically for debugging
            if self.offboard_setpoint_counter % 20 == 0:  # Every 2 seconds
                self.get_logger().info(f"Waiting for OFFBOARD+ARMED - Current: nav={self.vehicle_status.nav_state}, arm={self.vehicle_status.arming_state}")
            return

        # Execute flight phases
        if self.flight_phase == "ARMED":
            self.initial_x_position = self.vehicle_local_position.x
            self.flight_phase = "TAKEOFF"
            self.get_logger().info("Starting takeoff...")

        elif self.flight_phase == "TAKEOFF":
            # Check if we've reached takeoff altitude
            if abs(self.vehicle_local_position.z - self.takeoff_height) < 0.5:
                self.flight_phase = "BACKWARD"
                self.start_backward_time = time.time()
                self.get_logger().info("Starting backward flight...")

        elif self.flight_phase == "BACKWARD":
            elapsed = time.time() - self.start_backward_time
            if elapsed >= self.backward_duration:
                self.flight_phase = "LAND"
                self.get_logger().info("Landing...")
                self.land()

        elif self.flight_phase == "LAND":
            self.flight_phase = "DONE"


def main(args=None) -> None:
    print('Starting enemy offboard control node...')
    rclpy.init(args=args)
    enemy_offboard_control = EnemyOffboardControl()
    rclpy.spin(enemy_offboard_control)
    enemy_offboard_control.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)