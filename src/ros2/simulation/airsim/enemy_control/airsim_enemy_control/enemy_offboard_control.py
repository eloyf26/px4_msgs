#!/usr/bin/env python3

import math
import time
import random
import rclpy
from rclpy.node import Node
import airsim
import threading
try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class AirSimEnemyControl(Node):
    """Node for controlling the enemy drone movement patterns using AirSim API."""

    def __init__(self) -> None:
        super().__init__('airsim_enemy_offboard_control')

        # Declare parameters
        self.declare_parameter('pattern', 'circle')  # circle, figure8, random, keyboard
        self.declare_parameter('duration', 0.0)  # 0 means non-stop

        # Get parameters
        self.pattern = self.get_parameter('pattern').value
        self.duration = self.get_parameter('duration').value

        # Validate pattern
        valid_patterns = ['circle', 'figure8', 'random', 'keyboard']
        if self.pattern not in valid_patterns:
            self.get_logger().error(f"Invalid pattern: {self.pattern}. Using 'circle'.")
            self.pattern = 'circle'

        # Keyboard control requires pynput
        if self.pattern == 'keyboard' and not KEYBOARD_AVAILABLE:
            self.get_logger().error("Keyboard pattern requires 'pynput' library. Install with: pip3 install pynput")
            self.get_logger().error("Falling back to circle pattern")
            self.pattern = 'circle'

        self.get_logger().info(f"Enemy drone pattern: {self.pattern}, Duration: {self.duration}s (0=infinite)")

        # Connect to AirSim
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.get_logger().info("Connected to AirSim")

        # Enable API control for Enemy drone
        self.client.enableApiControl(True, "Enemy")
        self.client.armDisarm(True, "Enemy")

        # Takeoff Enemy drone
        self.get_logger().info("Taking off...")
        self.client.takeoffAsync(vehicle_name="Enemy").join()
        time.sleep(2)

        # Movement parameters
        self.start_time = time.time()
        self.current_altitude = -5.0  # AirSim NED frame (negative = up)

        # Pattern-specific parameters
        self.circle_radius = 50.0  # meters
        self.circle_speed = 1.0  # rad/s
        self.figure8_size = 50.0  # meters
        self.figure8_speed = 0.5  # rad/s
        self.random_speed = 2.0  # m/s
        self.random_bounds = 100.0  # meters
        self.random_target = None
        self.random_target_time = 0

        # Keyboard control parameters
        self.keyboard_velocity = [0.0, 0.0, 0.0]  # [x, y, z] velocity in m/s
        self.keyboard_step = 5.0  # m/s per key press
        self.keyboard_yaw_rate = 0.0  # rad/s
        self.keyboard_yaw_step = 0.5  # rad/s per key press
        self.keyboard_listener = None
        self.current_position = [0.0, 0.0, self.current_altitude]  # Track current position

        # Setup keyboard listener if keyboard pattern
        if self.pattern == 'keyboard':
            self.setup_keyboard_listener()
            self.get_logger().info('Keyboard controls:')
            self.get_logger().info('  W/S: Forward/Backward')
            self.get_logger().info('  A/D: Left/Right')
            self.get_logger().info('  Q/E: Yaw Left/Right')
            self.get_logger().info('  R/F: Up/Down')
            self.get_logger().info('  SPACE: Stop all movement')

        # Create a timer to update position at 10Hz
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info('AirSim Enemy control node initialized')

    def get_circle_position(self, t: float):
        """Calculate position for circular pattern."""
        angle = self.circle_speed * t
        x = self.circle_radius * math.cos(angle)
        y = self.circle_radius * math.sin(angle)
        z = self.current_altitude
        return x, y, z

    def get_figure8_position(self, t: float):
        """Calculate position for figure-8 pattern (horizontal infinity symbol)."""
        angle = self.figure8_speed * t
        scale = self.figure8_size / 2

        # Lemniscate parametric equations
        denominator = 1 + math.sin(angle) ** 2
        x = scale * 2 * math.cos(angle) / denominator
        y = scale * 2 * math.sin(angle) * math.cos(angle) / denominator
        z = self.current_altitude
        return x, y, z

    def get_random_position(self, t: float):
        """Calculate position for random movement pattern."""
        # Generate new random target every 5 seconds
        if self.random_target is None or t - self.random_target_time > 5.0:
            self.random_target = (
                random.uniform(-self.random_bounds/2, self.random_bounds/2),
                random.uniform(-self.random_bounds/2, self.random_bounds/2),
                self.current_altitude
            )
            self.random_target_time = t
            self.get_logger().info(f"New random target: ({self.random_target[0]:.1f}, {self.random_target[1]:.1f})")

        return self.random_target

    def setup_keyboard_listener(self):
        """Setup keyboard listener for manual control."""
        def on_press(key):
            try:
                if hasattr(key, 'char'):
                    if key.char == 'w':
                        self.keyboard_velocity[0] = self.keyboard_step
                    elif key.char == 's':
                        self.keyboard_velocity[0] = -self.keyboard_step
                    elif key.char == 'a':
                        self.keyboard_velocity[1] = -self.keyboard_step
                    elif key.char == 'd':
                        self.keyboard_velocity[1] = self.keyboard_step
                    elif key.char == 'r':
                        self.keyboard_velocity[2] = -self.keyboard_step  # negative = up in NED
                    elif key.char == 'f':
                        self.keyboard_velocity[2] = self.keyboard_step  # positive = down in NED
                    elif key.char == 'q':
                        self.keyboard_yaw_rate = -self.keyboard_yaw_step
                    elif key.char == 'e':
                        self.keyboard_yaw_rate = self.keyboard_yaw_step
                elif key == keyboard.Key.space:
                    # Stop all movement
                    self.keyboard_velocity = [0.0, 0.0, 0.0]
                    self.keyboard_yaw_rate = 0.0
            except AttributeError:
                pass

        def on_release(key):
            try:
                if hasattr(key, 'char'):
                    if key.char in ['w', 's']:
                        self.keyboard_velocity[0] = 0.0
                    elif key.char in ['a', 'd']:
                        self.keyboard_velocity[1] = 0.0
                    elif key.char in ['r', 'f']:
                        self.keyboard_velocity[2] = 0.0
                    elif key.char in ['q', 'e']:
                        self.keyboard_yaw_rate = 0.0
            except AttributeError:
                pass

        # Start the listener in a separate thread
        self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.keyboard_listener.start()

    def timer_callback(self) -> None:
        """Callback function for the timer."""
        # Check if duration has expired
        elapsed = time.time() - self.start_time
        if self.duration > 0 and elapsed >= self.duration:
            self.get_logger().info(f"Duration of {self.duration}s completed. Landing.")
            self.client.landAsync(vehicle_name="Enemy").join()
            self.timer.cancel()
            return

        # Get target position based on pattern
        if self.pattern == 'keyboard':
            # For keyboard control, use velocity commands
            dt = 0.1  # timer period

            # Update position based on velocity
            self.current_position[0] += self.keyboard_velocity[0] * dt
            self.current_position[1] += self.keyboard_velocity[1] * dt
            self.current_position[2] += self.keyboard_velocity[2] * dt

            # Keep altitude within reasonable bounds
            self.current_position[2] = max(-50.0, min(-2.0, self.current_position[2]))

            # Move to updated position
            self.client.moveToPositionAsync(
                self.current_position[0],
                self.current_position[1],
                self.current_position[2],
                5,
                vehicle_name="Enemy"
            )
        elif self.pattern == 'circle':
            x, y, z = self.get_circle_position(elapsed)
            self.client.moveToPositionAsync(x, y, z, 5, vehicle_name="Enemy")
        elif self.pattern == 'figure8':
            x, y, z = self.get_figure8_position(elapsed)
            self.client.moveToPositionAsync(x, y, z, 5, vehicle_name="Enemy")
        elif self.pattern == 'random':
            x, y, z = self.get_random_position(elapsed)
            self.client.moveToPositionAsync(x, y, z, 5, vehicle_name="Enemy")


def get_user_input():
    """Get movement pattern and duration from user interactively."""
    print('\n=========================================')
    print('   ENEMY DRONE MOVEMENT CONTROL (AirSim)')
    print('=========================================')
    print()
    print('Select movement pattern:')
    print('  1 - Circular movement')
    print('  2 - Figure-8 movement')
    print('  3 - Random movement')
    print('  4 - Keyboard control')
    print()
    print('Press 1, 2, 3, or 4 (or any other key for default circular):')

    pattern_input = input().strip()

    pattern_map = {
        '1': 'circle',
        '2': 'figure8',
        '3': 'random',
        '4': 'keyboard'
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
    airsim_enemy_control = AirSimEnemyControl()

    try:
        rclpy.spin(airsim_enemy_control)
    except KeyboardInterrupt:
        airsim_enemy_control.get_logger().info('Interrupted by user')
    finally:
        # Land and cleanup
        airsim_enemy_control.client.landAsync(vehicle_name="Enemy").join()
        airsim_enemy_control.client.armDisarm(False, "Enemy")
        airsim_enemy_control.client.enableApiControl(False, "Enemy")

        # Stop keyboard listener if active
        if airsim_enemy_control.keyboard_listener is not None:
            airsim_enemy_control.keyboard_listener.stop()

        airsim_enemy_control.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
