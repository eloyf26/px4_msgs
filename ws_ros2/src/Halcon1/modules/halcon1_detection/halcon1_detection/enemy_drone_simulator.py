import numpy as np

class EnemyDroneSimulator:
    def __init__(self):
        self.start_time = None  # Will be set on first call
        self.mode = 'circular'  # circular, linear, evasive

        # Initial position in NED world frame (meters)
        self.initial_position = np.array([10.0, 5.0, -5.0])  # 10m north, 5m east, 5m up
        self.velocity = np.array([2.0, 0.0, 0.0])  # 2 m/s north initially

    def get_world_position(self, current_time_sec=0):
        """Get enemy drone position in NED world frame

        Args:
            current_time_sec: Current simulation time in seconds
        """
        if self.start_time is None:
            self.start_time = current_time_sec

        t = current_time_sec - self.start_time

        if self.mode == 'circular':
            # Circular motion in horizontal plane
            radius = 8.0  # meters
            angular_speed = 0.3  # rad/s
            x = self.initial_position[0] + radius * np.cos(angular_speed * t)
            y = self.initial_position[1] + radius * np.sin(angular_speed * t)
            z = self.initial_position[2]  # constant altitude

        elif self.mode == 'linear':
            # Straight line motion
            x = self.initial_position[0] + self.velocity[0] * t
            y = self.initial_position[1] + self.velocity[1] * t
            z = self.initial_position[2] + self.velocity[2] * t

        elif self.mode == 'evasive':
            # Sinusoidal evasive maneuvers
            x = self.initial_position[0] + 2.0 * t
            y = self.initial_position[1] + 5.0 * np.sin(0.5 * t)
            z = self.initial_position[2] + 2.0 * np.sin(0.3 * t)

        else:
            x, y, z = self.initial_position

        return np.array([x, y, z])

    def project_to_camera(self, enemy_pos_ned, friendly_pos_ned, friendly_quaternion=None):
        """
        Project enemy position to camera pixel coordinates
        Assumes camera is forward-facing on the friendly drone
        """
        # Relative position in NED frame
        relative_ned = enemy_pos_ned - friendly_pos_ned

        # Simple projection (assuming camera points north for now)
        # In reality, would use quaternion to rotate to body frame first

        # Camera parameters
        focal_length = 500  # pixels
        cx, cy = 320, 240  # image center

        # Simple pinhole projection (assuming enemy is in front)
        if relative_ned[0] > 0.1:  # enemy is ahead (north)
            pixel_x = cx - (relative_ned[1] / relative_ned[0]) * focal_length
            pixel_y = cy + (relative_ned[2] / relative_ned[0]) * focal_length

            # Add measurement noise
            pixel_x += np.random.normal(0, 3)
            pixel_y += np.random.normal(0, 3)

            # Check if in frame
            if 0 <= pixel_x < 640 and 0 <= pixel_y < 480:
                return pixel_x, pixel_y, 0.95  # high confidence
            else:
                return 320, 240, 0.0  # out of frame
        else:
            return 320, 240, 0.0  # behind drone