import numpy as np
from halcon1_types import DronePose
from dataclasses import dataclass

@dataclass
class KalmanFilterParameters:
    process_noise: float = 0.1  # Process noise intensity
    measurement_noise_position: float = 1.0  # Measurement noise for position

class KalmanFilter:
    def __init__(self, params: KalmanFilterParameters):
        self.process_noise = params.process_noise
        self.measurement_noise_position = params.measurement_noise_position

        self.previous_estimate = None
        self.latest_timestamp = None

    def update(self, measurement: DronePose, timestamp: float) -> DronePose:
        if self.previous_estimate is None:
            # First measurement, initialize state
            self.previous_estimate = measurement
            self.latest_timestamp = timestamp
            return measurement

        # Compute dt
        dt = timestamp - self.latest_timestamp
        self.latest_timestamp = timestamp

        estimate = measurement # For now we don't actually run KF, when we run KF dt will be used here.

        # Update previous estimate (used in KF)
        self.previous_estimate = estimate

        return estimate
