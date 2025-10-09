#!/usr/bin/env python3
"""
RViz2 Distance Calculator
Subscribes to /clicked_point topic and calculates distances between consecutive clicks.
Usage: Run this script, then use the "Publish Point" tool in RViz2 to click points.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped
import math


class DistanceCalculator(Node):
    def __init__(self):
        super().__init__('rviz_distance_calculator')

        self.subscription = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.point_callback,
            10
        )

        self.last_point = None
        self.point_count = 0

        self.get_logger().info('Distance Calculator started!')
        self.get_logger().info('Use "Publish Point" tool in RViz2 to click points.')
        self.get_logger().info('Distance will be calculated between consecutive clicks.')
        self.get_logger().info('-' * 60)

    def point_callback(self, msg: PointStamped):
        self.point_count += 1
        current_point = msg.point

        self.get_logger().info(f'Point {self.point_count}: x={current_point.x:.3f}, '
                              f'y={current_point.y:.3f}, z={current_point.z:.3f} '
                              f'(frame: {msg.header.frame_id})')

        if self.last_point is not None:
            # Calculate distance
            dx = current_point.x - self.last_point.x
            dy = current_point.y - self.last_point.y
            dz = current_point.z - self.last_point.z

            distance = math.sqrt(dx**2 + dy**2 + dz**2)
            distance_xy = math.sqrt(dx**2 + dy**2)  # Horizontal distance

            self.get_logger().info(f'📏 DISTANCE: {distance:.4f} meters')
            self.get_logger().info(f'   ├─ Horizontal (XY): {distance_xy:.4f} m')
            self.get_logger().info(f'   ├─ Vertical (Z):    {abs(dz):.4f} m')
            self.get_logger().info(f'   └─ Delta: dx={dx:.3f}, dy={dy:.3f}, dz={dz:.3f}')
            self.get_logger().info('-' * 60)
        else:
            self.get_logger().info('   (First point - click another point to measure distance)')
            self.get_logger().info('-' * 60)

        self.last_point = current_point


def main(args=None):
    rclpy.init(args=args)
    calculator = DistanceCalculator()

    try:
        rclpy.spin(calculator)
    except KeyboardInterrupt:
        pass
    finally:
        calculator.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
