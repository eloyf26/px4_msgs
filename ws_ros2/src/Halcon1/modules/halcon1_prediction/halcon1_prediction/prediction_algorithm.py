import numpy as np

class PredictionAlgorithm:
    def __init__(self):
        self.prediction_horizon = 5.0  # seconds
        self.num_points = 10
        self.dt = self.prediction_horizon / self.num_points

    def predict_trajectory(self, position, velocity):
        # Linear prediction: p(t) = p0 + v * t
        times = []
        x_points = []
        y_points = []
        z_points = []

        for i in range(self.num_points):
            t = (i + 1) * self.dt
            times.append(t)
            x_points.append(position[0] + velocity[0] * t)
            y_points.append(position[1] + velocity[1] * t)
            z_points.append(position[2] + velocity[2] * t)

        return {
            'times': times,
            'x': x_points,
            'y': y_points,
            'z': z_points
        }