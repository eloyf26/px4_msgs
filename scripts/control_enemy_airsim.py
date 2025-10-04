#!/usr/bin/env python3

"""
Enemy Drone Control Script for AirSim Multi-Drone Simulation

This script controls the Enemy drone using AirSim SimpleFlight API.
The Ally drone is controlled by PX4 and tracks/intercepts this enemy drone.

Movement patterns:
1. Circular - Enemy flies in a circle
2. Figure-8 - Enemy flies in a figure-8 pattern
3. Random - Enemy moves randomly
4. Hover - Enemy hovers at current position
"""

import airsim
import time
import math
import sys
import argparse
import numpy as np
from datetime import datetime


class EnemyDroneController:
    def __init__(self, vehicle_name="Enemy", host_ip="127.0.0.1"):
        """Initialize AirSim client and connect to Enemy drone."""
        self.vehicle_name = vehicle_name
        self.client = airsim.MultirotorClient(ip=host_ip)
        self.client.confirmConnection()

        # Enable API control for Enemy drone
        self.client.enableApiControl(True, vehicle_name=self.vehicle_name)

        print(f"✅ Connected to AirSim at {host_ip}")
        print(f"✅ API control enabled for '{self.vehicle_name}'")

        # Movement parameters
        self.altitude = -5.0  # 5 meters above ground (NED: negative is up)
        self.speed = 3.0      # m/s
        self.radius = 8.0     # Circle radius in meters

    def arm_and_takeoff(self, target_altitude=-5.0):
        """Arm the drone and takeoff to target altitude."""
        print(f"\n🚁 Arming '{self.vehicle_name}'...")
        self.client.armDisarm(True, vehicle_name=self.vehicle_name)
        time.sleep(1)

        print(f"🚁 Taking off to {abs(target_altitude)} meters...")
        self.client.takeoffAsync(vehicle_name=self.vehicle_name).join()

        # Move to target altitude
        self.client.moveToZAsync(target_altitude, velocity=2,
                                  vehicle_name=self.vehicle_name).join()

        print(f"✅ '{self.vehicle_name}' ready at altitude {abs(target_altitude)}m")
        self.altitude = target_altitude

    def land_and_disarm(self):
        """Land the drone and disarm."""
        print(f"\n🛬 Landing '{self.vehicle_name}'...")
        self.client.landAsync(vehicle_name=self.vehicle_name).join()

        print(f"🔓 Disarming '{self.vehicle_name}'...")
        self.client.armDisarm(False, vehicle_name=self.vehicle_name)

        print(f"✅ '{self.vehicle_name}' landed and disarmed")

    def hover(self, duration=None):
        """Hover at current position."""
        print(f"\n🔵 HOVER MODE: '{self.vehicle_name}' hovering...")

        # Get current position
        state = self.client.getMultirotorState(vehicle_name=self.vehicle_name)
        pos = state.kinematics_estimated.position

        print(f"   Position: X={pos.x_val:.1f}, Y={pos.y_val:.1f}, Z={pos.z_val:.1f}")

        if duration:
            print(f"   Duration: {duration} seconds")
            time.sleep(duration)
        else:
            print("   Press Ctrl+C to stop...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️  Hover stopped")

    def circular_movement(self, duration=None, radius=None, speed=None):
        """Fly in a circular pattern."""
        if radius is None:
            radius = self.radius
        if speed is None:
            speed = self.speed

        print(f"\n🔵 CIRCULAR MODE: Radius={radius}m, Speed={speed}m/s")
        if duration:
            print(f"   Duration: {duration} seconds")
        else:
            print("   Press Ctrl+C to stop...")

        # Get starting position
        state = self.client.getMultirotorState(vehicle_name=self.vehicle_name)
        center_x = state.kinematics_estimated.position.x_val
        center_y = state.kinematics_estimated.position.y_val

        # Calculate angular velocity (rad/s)
        angular_velocity = speed / radius

        start_time = time.time()
        angle = 0

        try:
            while True:
                # Calculate target position on circle
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                z = self.altitude

                # Move to position
                self.client.moveToPositionAsync(
                    x, y, z,
                    velocity=speed,
                    vehicle_name=self.vehicle_name
                )

                # Update angle
                angle += angular_velocity * 0.1  # Update every 0.1 seconds

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    print("\n✅ Circular movement completed")
                    break

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n⏹️  Circular movement stopped")

    def figure8_movement(self, duration=None, radius=None, speed=None):
        """Fly in a figure-8 pattern."""
        if radius is None:
            radius = self.radius
        if speed is None:
            speed = self.speed

        print(f"\n🔵 FIGURE-8 MODE: Radius={radius}m, Speed={speed}m/s")
        if duration:
            print(f"   Duration: {duration} seconds")
        else:
            print("   Press Ctrl+C to stop...")

        # Get starting position
        state = self.client.getMultirotorState(vehicle_name=self.vehicle_name)
        center_x = state.kinematics_estimated.position.x_val
        center_y = state.kinematics_estimated.position.y_val

        # Calculate angular velocity
        angular_velocity = speed / radius

        start_time = time.time()
        t = 0

        try:
            while True:
                # Figure-8 parametric equations (Lemniscate of Gerono)
                # x = a * cos(t)
                # y = a * sin(2*t) / 2
                x = center_x + radius * math.cos(t)
                y = center_y + (radius * math.sin(2 * t) / 2)
                z = self.altitude

                # Move to position
                self.client.moveToPositionAsync(
                    x, y, z,
                    velocity=speed,
                    vehicle_name=self.vehicle_name
                )

                # Update parameter
                t += angular_velocity * 0.1
                if t > 2 * math.pi:
                    t -= 2 * math.pi

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    print("\n✅ Figure-8 movement completed")
                    break

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n⏹️  Figure-8 movement stopped")

    def random_movement(self, duration=None, bounds=15.0, speed=None):
        """Fly to random positions within bounds."""
        if speed is None:
            speed = self.speed

        print(f"\n🔵 RANDOM MODE: Bounds=±{bounds}m, Speed={speed}m/s")
        if duration:
            print(f"   Duration: {duration} seconds")
        else:
            print("   Press Ctrl+C to stop...")

        # Get starting position
        state = self.client.getMultirotorState(vehicle_name=self.vehicle_name)
        center_x = state.kinematics_estimated.position.x_val
        center_y = state.kinematics_estimated.position.y_val

        start_time = time.time()

        try:
            while True:
                # Generate random target position
                x = center_x + np.random.uniform(-bounds, bounds)
                y = center_y + np.random.uniform(-bounds, bounds)
                z = self.altitude

                print(f"   → Moving to ({x:.1f}, {y:.1f}, {z:.1f})")

                # Move to position and wait
                self.client.moveToPositionAsync(
                    x, y, z,
                    velocity=speed,
                    vehicle_name=self.vehicle_name
                ).join()

                # Hover briefly at position
                time.sleep(2)

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    print("\n✅ Random movement completed")
                    break

        except KeyboardInterrupt:
            print("\n⏹️  Random movement stopped")

    def waypoint_movement(self, waypoints, speed=None):
        """Fly through a list of waypoints."""
        if speed is None:
            speed = self.speed

        print(f"\n🔵 WAYPOINT MODE: {len(waypoints)} waypoints, Speed={speed}m/s")

        for i, (x, y, z) in enumerate(waypoints, 1):
            print(f"   → Waypoint {i}/{len(waypoints)}: ({x}, {y}, {z})")
            self.client.moveToPositionAsync(
                x, y, z,
                velocity=speed,
                vehicle_name=self.vehicle_name
            ).join()
            time.sleep(1)

        print("✅ All waypoints completed")

    def stop(self):
        """Disable API control and disconnect."""
        print(f"\n🛑 Disabling API control for '{self.vehicle_name}'...")
        self.client.enableApiControl(False, vehicle_name=self.vehicle_name)
        print("✅ Disconnected")


def print_menu():
    """Print movement pattern menu."""
    print("\n" + "="*50)
    print("  ENEMY DRONE CONTROL - AirSim Multi-Drone")
    print("="*50)
    print("\nMovement Patterns:")
    print("  1. Circular    - Fly in a circle")
    print("  2. Figure-8    - Fly in a figure-8 pattern")
    print("  3. Random      - Move to random positions")
    print("  4. Hover       - Hover at current position")
    print("  5. Land        - Land and disarm")
    print("  q. Quit        - Exit program")
    print("\n" + "="*50)


def main():
    parser = argparse.ArgumentParser(description="Control Enemy drone in AirSim")
    parser.add_argument("--host", default="127.0.0.1", help="AirSim host IP")
    parser.add_argument("--vehicle", default="Enemy", help="Vehicle name")
    parser.add_argument("--altitude", type=float, default=5.0, help="Flight altitude (meters)")
    parser.add_argument("--speed", type=float, default=3.0, help="Flight speed (m/s)")
    parser.add_argument("--radius", type=float, default=8.0, help="Circle/Figure-8 radius (meters)")
    parser.add_argument("--auto", type=int, choices=[1,2,3,4],
                       help="Auto mode: 1=Circular, 2=Figure-8, 3=Random, 4=Hover")
    parser.add_argument("--duration", type=float, help="Duration in seconds (0=infinite)")

    args = parser.parse_args()

    try:
        # Initialize controller
        controller = EnemyDroneController(vehicle_name=args.vehicle, host_ip=args.host)
        controller.altitude = -abs(args.altitude)
        controller.speed = args.speed
        controller.radius = args.radius

        # Arm and takeoff
        controller.arm_and_takeoff(target_altitude=controller.altitude)

        # Auto mode (non-interactive)
        if args.auto:
            duration = args.duration if args.duration and args.duration > 0 else None

            if args.auto == 1:
                controller.circular_movement(duration=duration)
            elif args.auto == 2:
                controller.figure8_movement(duration=duration)
            elif args.auto == 3:
                controller.random_movement(duration=duration)
            elif args.auto == 4:
                controller.hover(duration=duration)

            controller.land_and_disarm()
            controller.stop()
            return

        # Interactive mode
        while True:
            print_menu()
            choice = input("\nSelect movement pattern: ").strip()

            if choice == '1':
                duration_str = input("Duration (seconds, Enter=infinite): ").strip()
                duration = float(duration_str) if duration_str else None
                controller.circular_movement(duration=duration)

            elif choice == '2':
                duration_str = input("Duration (seconds, Enter=infinite): ").strip()
                duration = float(duration_str) if duration_str else None
                controller.figure8_movement(duration=duration)

            elif choice == '3':
                duration_str = input("Duration (seconds, Enter=infinite): ").strip()
                duration = float(duration_str) if duration_str else None
                controller.random_movement(duration=duration)

            elif choice == '4':
                duration_str = input("Duration (seconds, Enter=infinite): ").strip()
                duration = float(duration_str) if duration_str else None
                controller.hover(duration=duration)

            elif choice == '5':
                controller.land_and_disarm()
                controller.stop()
                break

            elif choice.lower() == 'q':
                controller.land_and_disarm()
                controller.stop()
                break

            else:
                print("❌ Invalid choice. Please try again.")

    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
        controller.land_and_disarm()
        controller.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
