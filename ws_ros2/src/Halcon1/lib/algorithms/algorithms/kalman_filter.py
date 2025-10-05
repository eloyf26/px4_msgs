import numpy as np
from dataclasses import dataclass

@dataclass
class KalmanFilterParameters:
    process_noise: float = 0.1  # Process noise intensity (i.e. wind)
    sigma_pos: float = 0.5  # Measurement noise standard deviation (position)

class KalmanFilter:
    """
    Constant velocity model kalman filter. Variable delta time (dt) is used in each predict/update call.
    """
    def __init__(self, params: KalmanFilterParameters):
        self.params = params

        # State: [x, y, z, vx, vy, vz, ax, ay, az]
        self.state = np.zeros(9)
        self.P = np.eye(9) * 100.0  # Initial covariance

        self.latest_update_millis = None

        # Observation matrix (we only observe position)
        self.H = np.zeros((3, 9))
        self.H[0, 0] = 1
        self.H[1, 1] = 1
        self.H[2, 2] = 1

        # Measurement noise covariance
        variance_pos = self.params.sigma_pos**2
        self.R = np.diag([variance_pos, variance_pos, variance_pos])

    @staticmethod
    def _get_state_transition_matrix(dt: float) -> np.ndarray:
        """
        Create state transition matrix for constant acceleration model.
        State: [x, y, z, vx, vy, vz, ax, ay, az]
        """
        F = np.eye(9)
        # Position = position + velocity * dt + 0.5 * acceleration * dt^2
        F[0:3, 3:6] = np.eye(3) * dt
        F[0:3, 6:9] = np.eye(3) * 0.5 * dt**2
        # Velocity = velocity + acceleration * dt
        F[3:6, 6:9] = np.eye(3) * dt
        return F

    @staticmethod
    def _get_process_noise_covariance(dt: float, q: float) -> np.ndarray:
        """
        Process noise covariance matrix for constant acceleration model.
        q: process noise intensity
        """
        Q = np.zeros((9, 9))
        dt2 = dt * dt
        dt3 = dt2 * dt
        dt4 = dt3 * dt

        # Position noise
        Q[0:3, 0:3] = np.eye(3) * (dt4 / 4.0) * q
        # Cross terms position-velocity
        Q[0:3, 3:6] = np.eye(3) * (dt3 / 2.0) * q
        Q[3:6, 0:3] = Q[0:3, 3:6].T
        # Velocity noise
        Q[3:6, 3:6] = np.eye(3) * dt2 * q
        # Cross terms velocity-acceleration
        Q[3:6, 6:9] = np.eye(3) * dt * q
        Q[6:9, 3:6] = Q[3:6, 6:9].T
        # Acceleration noise
        Q[6:9, 6:9] = np.eye(3) * q

        return Q

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

        return self.state[:3], self.state[3:6]

    def update(self, measurement: np.ndarray, current_time_millis: int):
        """
        Update step of Kalman filter
        Given a new measurement (position only), update the state and covariance.
        """

        dt = (current_time_millis - self.latest_update_millis) / 1000.0 if self.latest_update_millis is not None else 0.1
        self.latest_update_millis = current_time_millis

        F = self._get_state_transition_matrix(dt)
        Q = self._get_process_noise_covariance(dt, self.params.process_noise)
        self.state = F @ self.state
        self.P = F @ self.P @ F.T + Q

        # Full state measurement (position + velocity)
        innovation = measurement - self.H @ self.state
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K @ innovation
        
        # Update covariance
        self.P = (np.eye(9) - K @ self.H) @ self.P
