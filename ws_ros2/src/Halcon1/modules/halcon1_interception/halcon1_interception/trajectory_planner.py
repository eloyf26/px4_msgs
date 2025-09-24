import numpy as np

from halcon1_types import TimestampedTrajectory, DronePose
from dataclasses import dataclass

@dataclass
class TrajectoryPlannerParameters:
    max_velocity: float = 10.0 # m / s
    max_acceleration: float = 5.0 # m / s^2
    safety_margin: float = 0.5 # meters

class TrajectoryPlanner:
    def __init__(self, params: TrajectoryPlannerParameters):
        # Drone dynamics constraints
        self.max_velocity = params.max_velocity
        self.max_acceleration = params.max_acceleration
        self.safety_margin = params.safety_margin

    def plan_interception(self, enemy_trajectory: TimestampedTrajectory, friendly_position: DronePose) -> TimestampedTrajectory:

        # For now, we will just generate a straight line trajectory to the last known enemy position.
        if len(enemy_trajectory.positions) == 0:
            return TimestampedTrajectory([], [])

        # Get target position from enemy trajectory
        target_position = np.array([enemy_trajectory.positions[-1].x,
                                    enemy_trajectory.positions[-1].y,
                                    enemy_trajectory.positions[-1].z])

        # Get friendly position as numpy array
        friendly_pos_np = np.array([friendly_position.x, friendly_position.y, friendly_position.z])

        # Calculate direction and distance
        direction = target_position - friendly_pos_np
        distance = np.linalg.norm(direction)

        if distance < self.safety_margin:
            return TimestampedTrajectory([], [])

        direction /= distance  # Normalize
        travel_time = distance / self.max_velocity

        # Generate timestamped trajectory points at 50 Hz
        dt = 1.0 / 50.0  # 50 Hz
        num_points = int(travel_time / dt)

        timestamps = []
        positions = []

        # Use the last timestamp from enemy trajectory as starting point
        start_time = enemy_trajectory.timestamps[-1] if enemy_trajectory.timestamps else 0.0

        for i in range(num_points):
            t = i * dt
            timestamp = start_time + t

            # Calculate position along trajectory
            travel_distance = min(self.max_velocity * t, distance - self.safety_margin)
            position_np = friendly_pos_np + direction * travel_distance

            # Convert to DronePose
            position = DronePose(
                x=float(position_np[0]),
                y=float(position_np[1]),
                z=float(position_np[2])
            )

            timestamps.append(timestamp)
            positions.append(position)

        return TimestampedTrajectory(timestamps, positions)