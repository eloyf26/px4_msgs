import numpy as np
from dataclasses import dataclass

@dataclass
class KalmanFilterParameters:
    process_noise: float = 0.1  # Process noise intensity
    sigma_pos: float = 0.5  # Measurement noise standard deviation (position)

class KalmanFilter:
    """
    Constant velocity model kalman filter. Variable delta time (dt) is used in each predict/update call.
    """
    def __init__(self, params: KalmanFilterParameters):
        self.params = params

        # State: [x, y, z, vx, vy, vz]
        self.state = np.zeros(6)
        self.P = np.eye(6) * 100.0  # Initial covariance

        self.latest_update_millis = None

        # Observation matrix (we only observe position)
        self.H = np.zeros((3, 6))
        self.H[0, 0] = 1
        self.H[1, 1] = 1
        self.H[2, 2] = 1

        # Measurement noise covariance
        variance_pos = self.params.sigma_pos**2
        self.R = np.diag([variance_pos, variance_pos, variance_pos])

    @staticmethod
    def _get_state_transition_matrix(dt: float) -> np.ndarray:
        """
        Create state transition matrix for constant velocity model.
        State: [x, y, z, vx, vy, vz]
        """
        F = np.eye(6)
        F[0:3, 3:6] = np.eye(3) * dt
        return F

    def predict(self, current_time_millis: int) -> (np.ndarray, np.ndarray):
        """
        Predict step of Kalman filter.
        Uses the current state and the constant velocity model to predict the state at time current_time_millis.
        Retuns a tuple with the estimated position and estimated velocity.
        """

        dt = (current_time_millis - self.latest_update_millis) / 1000.0 if self.latest_update_millis is not None else 0.1
        self.latest_update_millis = current_time_millis

        F = self._get_state_transition_matrix(dt)
        self.state = F @ self.state

        return self.state[:3], self.state[3:]


    def update(self, measurement: np.ndarray, current_time_millis: int):
        """
        Update step of Kalman filter
        Given a new measurement (position only), update the state and covariance.
        """

        dt = (current_time_millis - self.latest_update_millis) / 1000.0 if self.latest_update_millis is not None else 0.1
        self.latest_update_millis = current_time_millis

        F = self._get_state_transition_matrix(dt)
        self.state = F @ self.state
        self.P = F @ self.P @ F.T

        # Full state measurement (position + velocity)
        innovation = measurement - self.H @ self.state
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K @ innovation
        
        # Update covariance
        self.P = (np.eye(6) - K @ self.H) @ self.P

