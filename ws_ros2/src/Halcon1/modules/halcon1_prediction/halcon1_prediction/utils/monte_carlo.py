import numpy as np
from halcon1_types import TimestampedTrajectory, DronePose
from dataclasses import dataclass

@dataclass
class MonteCarloParameters:
    num_samples: int = 50
    time_horizeon: float = 3.0

class MonteCarloPredictor:
    def __init__(self, params: MonteCarloParameters):
        self.num_samples = params.num_samples
        self.time_horizon = params.time_horizeon

    def update(self, trajectory: TimestampedTrajectory):
        # Given a trajectory, generate N samples of future trajectories and return their average.

        # For now we just return a very simple constant velocity model.
        if len(trajectory.timestamps) < 2:
            return trajectory
        speed = np.array([
            (trajectory.positions[-1].x - trajectory.positions[-2].x) / (trajectory.timestamps[-1] - trajectory.timestamps[-2]),
            (trajectory.positions[-1].y - trajectory.positions[-2].y) / (trajectory.timestamps[-1] - trajectory.timestamps[-2]),
            (trajectory.positions[-1].z - trajectory.positions[-2].z) / (trajectory.timestamps[-1] - trajectory.timestamps[-2]),
        ])
        last_position = trajectory.positions[-1]
        last_timestamp = trajectory.timestamps[-1]
        future_timestamps = np.linspace(last_timestamp, last_timestamp + self.time_horizon, num=10)
        future_positions = []
        for t in future_timestamps:
            dt = t - last_timestamp
            future_positions.append(np.array([
                last_position.x + speed[0] * dt,
                last_position.y + speed[1] * dt,
                last_position.z + speed[2] * dt,
            ]))

        future_trajectory = TimestampedTrajectory(
            timestamps = future_timestamps.tolist(),
            positions = [DronePose(x=pos[0], y=pos[1], z=pos[2]) for pos in future_positions]
        )
        return future_trajectory