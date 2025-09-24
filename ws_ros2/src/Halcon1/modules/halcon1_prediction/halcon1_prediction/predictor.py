from halcon1_types import DronePose
import numpy as np
from halcon1_prediction.predictor.utils.kalman_filter import KalmanFilter, KalmanFilterParameters
from halcon1_prediction.predictor.utils.monte_carlo import MonteCarloPredictor, MonteCarloParameters

from halcon1_types import TimestampedTrajectory

class Predictor:

    def __init__(self, kf_params: KalmanFilterParameters, mc_params: MonteCarloParameters):
        self.estimated_trajectory = TimestampedTrajectory([], [])
        self.kf = KalmanFilter(kf_params)
        self.mc = MonteCarloPredictor(mc_params)

    def reinitialize(self):
        self.kf = KalmanFilter(self.kf.params)
        self.mc = MonteCarloPredictor(self.mc.params)
        self.estimated_trajectory = TimestampedTrajectory([], [])

    def predict(self, enemy_pose: DronePose, timestamp: float):
        # Add measurement update to Kalman filter
        measurement = np.array([
            enemy_pose.x, enemy_pose.y, enemy_pose.z
        ])
        
        estimated_state = self.kf.update(measurement, timestamp)

        self.estimated_trajectory.timestamps.append(timestamp)
        self.estimated_trajectory.positions.append(estimated_state)

        trajectory_prediction = self.mc.update(self.estimated_trajectory)

        return trajectory_prediction

