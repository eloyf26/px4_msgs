import numpy as np

class PX4CommandGenerator:
    def __init__(self):
        self.current_waypoint_idx = 0
        self.trajectory = None

    def set_trajectory(self, trajectory):
        """Set new trajectory to follow"""
        self.trajectory = trajectory
        self.current_waypoint_idx = 0

    def get_setpoint(self, current_time=0):
        """
        Generate PX4 trajectory setpoint for current time

        Returns:
            Dict with position, velocity, acceleration in NED frame
        """
        if self.trajectory is None or len(self.trajectory['waypoints']) == 0:
            return None

        # Find appropriate waypoint based on time
        waypoints = self.trajectory['waypoints']

        # Find current waypoint
        target_waypoint = None
        for i, wp in enumerate(waypoints):
            if wp['time'] >= current_time:
                target_waypoint = wp
                self.current_waypoint_idx = i
                break

        # If past all waypoints, use last one
        if target_waypoint is None:
            target_waypoint = waypoints[-1]

        # Create PX4 setpoint
        setpoint = {
            'position': target_waypoint['position'].tolist(),
            'velocity': target_waypoint['velocity'].tolist(),
            'acceleration': target_waypoint['acceleration'].tolist(),
            'yaw': 0.0,  # Face forward
            'yawspeed': 0.0
        }

        # Validate constraints
        vel_mag = np.linalg.norm(target_waypoint['velocity'])
        if vel_mag > 15.0:  # Safety limit
            scale = 15.0 / vel_mag
            setpoint['velocity'] = (target_waypoint['velocity'] * scale).tolist()

        acc_mag = np.linalg.norm(target_waypoint['acceleration'])
        if acc_mag > 10.0:  # Safety limit
            scale = 10.0 / acc_mag
            setpoint['acceleration'] = (target_waypoint['acceleration'] * scale).tolist()

        return setpoint

    def is_trajectory_complete(self, current_time):
        """Check if trajectory is complete"""
        if self.trajectory is None:
            return True

        duration = self.trajectory.get('duration', 0)
        return current_time >= duration