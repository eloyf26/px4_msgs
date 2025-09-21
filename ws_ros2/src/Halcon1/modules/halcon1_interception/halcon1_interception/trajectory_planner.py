import numpy as np

class TrajectoryPlanner:
    def __init__(self):
        # Drone dynamics constraints
        self.max_velocity = 10.0  # m/s
        self.max_acceleration = 5.0  # m/s^2
        self.safety_margin = 2.0  # meters

    def plan_interception(self, enemy_trajectory, friendly_position, friendly_velocity):
        """
        Plan optimal interception trajectory

        Args:
            enemy_trajectory: Dict with 'times', 'mean', 'upper', 'lower'
            friendly_position: Current position [x, y, z]
            friendly_velocity: Current velocity [vx, vy, vz]

        Returns:
            Interception trajectory with position, velocity, acceleration
        """
        if enemy_trajectory is None:
            return None

        # Find best interception point
        best_point, best_time = self.find_interception_point(
            enemy_trajectory, friendly_position
        )

        if best_point is None:
            return None

        # Generate minimum snap trajectory
        trajectory = self.generate_minimum_snap(
            friendly_position,
            friendly_velocity,
            best_point,
            best_time
        )

        return trajectory

    def find_interception_point(self, enemy_trajectory, friendly_pos):
        """Find optimal point to intercept enemy"""
        times = enemy_trajectory['times']
        mean_traj = enemy_trajectory['mean']

        best_point = None
        best_time = None
        min_cost = float('inf')

        for i, t in enumerate(times):
            target_pos = mean_traj[i]
            distance = np.linalg.norm(target_pos - friendly_pos)

            # Check if we can reach this point in time
            required_speed = distance / t
            if required_speed <= self.max_velocity:
                # Cost function: prefer earlier interception
                cost = t + 0.1 * distance
                if cost < min_cost:
                    min_cost = cost
                    best_point = target_pos
                    best_time = t

        return best_point, best_time

    def generate_minimum_snap(self, start_pos, start_vel, end_pos, duration):
        """
        Generate minimum snap trajectory (simplified version)
        Uses 5th order polynomial for smooth trajectory
        """
        if duration <= 0:
            return None

        # Coefficients for 5th order polynomial
        # p(t) = a0 + a1*t + a2*t^2 + a3*t^3 + a4*t^4 + a5*t^5
        T = duration
        T2 = T * T
        T3 = T2 * T
        T4 = T3 * T
        T5 = T4 * T

        # Boundary conditions
        # Position: p(0) = start_pos, p(T) = end_pos
        # Velocity: v(0) = start_vel, v(T) = 0
        # Acceleration: a(0) = 0, a(T) = 0

        trajectory = {
            'duration': duration,
            'coefficients': {},
            'waypoints': []
        }

        # Calculate coefficients for each axis
        for axis, label in enumerate(['x', 'y', 'z']):
            p0 = start_pos[axis]
            pf = end_pos[axis]
            v0 = start_vel[axis]

            # Simplified coefficients (assuming zero final velocity and acceleration)
            a0 = p0
            a1 = v0
            a2 = 0
            a3 = (10 * (pf - p0) - 6 * v0 * T) / T3
            a4 = (-15 * (pf - p0) + 8 * v0 * T) / T4
            a5 = (6 * (pf - p0) - 3 * v0 * T) / T5

            trajectory['coefficients'][label] = [a0, a1, a2, a3, a4, a5]

        # Generate waypoints
        num_waypoints = int(duration * 50)  # 50Hz
        dt = duration / num_waypoints

        for i in range(num_waypoints):
            t = i * dt
            t2 = t * t
            t3 = t2 * t
            t4 = t3 * t
            t5 = t4 * t

            waypoint = {
                'time': t,
                'position': np.zeros(3),
                'velocity': np.zeros(3),
                'acceleration': np.zeros(3)
            }

            for axis, label in enumerate(['x', 'y', 'z']):
                c = trajectory['coefficients'][label]

                # Position
                waypoint['position'][axis] = c[0] + c[1]*t + c[2]*t2 + c[3]*t3 + c[4]*t4 + c[5]*t5

                # Velocity
                waypoint['velocity'][axis] = c[1] + 2*c[2]*t + 3*c[3]*t2 + 4*c[4]*t3 + 5*c[5]*t4

                # Acceleration
                waypoint['acceleration'][axis] = 2*c[2] + 6*c[3]*t + 12*c[4]*t2 + 20*c[5]*t3

            trajectory['waypoints'].append(waypoint)

        return trajectory