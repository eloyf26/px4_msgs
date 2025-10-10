import numpy as np
from dataclasses import dataclass

@dataclass
class KalmanFilterParameters:
    # Environment-dependent parameters - fine-tunable for DEMO
    process_noise: float = 0.0  # Process noise intensity (i.e. wind)
    sigma_pos: float = 3.7  # Measurement noise standard deviation (position)

    use_constant_velocity_model: bool = True  # Use 6-state CV model instead of 9-state CA model

class KalmanFilter:
    """
    Kalman filter with support for Constant Velocity (CV) or Constant Acceleration (CA) models.
    Variable delta time (dt) is used in each predict/update call.
    - CV model: 6-state [x, y, z, vx, vy, vz]
    - CA model: 9-state [x, y, z, vx, vy, vz, ax, ay, az] (default)
    """
    def __init__(self, params: KalmanFilterParameters):
        self.params = params

        # Determine state size based on model type
        self.state_size = 6 if params.use_constant_velocity_model else 9

        # Initialize state vector
        # CV model: [x, y, z, vx, vy, vz]
        # CA model: [x, y, z, vx, vy, vz, ax, ay, az]
        self.state = np.zeros(self.state_size)
        self.P = np.eye(self.state_size) * 100.0  # Initial covariance

        self.latest_update_millis = None

        # Observation matrix (we only observe position)
        self.H = np.zeros((3, self.state_size))
        self.H[0, 0] = 1
        self.H[1, 1] = 1
        self.H[2, 2] = 1

        # Measurement noise covariance
        variance_pos = self.params.sigma_pos**2
        self.R = np.diag([variance_pos, variance_pos, variance_pos])

    def _get_state_transition_matrix(self, dt: float) -> np.ndarray:
        """
        Create state transition matrix for constant acceleration model.
        State: [x, y, z, vx, vy, vz, ax, ay, az]
        """
        F = np.eye(self.state_size)
        if self.params.use_constant_velocity_model:
            # Position = position + velocity * dt
            F[0:3, 3:6] = np.eye(3) * dt
        else:
            # Position = position + velocity * dt + 0.5 * acceleration * dt^2
            F[0:3, 3:6] = np.eye(3) * dt
            F[0:3, 6:9] = np.eye(3) * 0.5 * dt**2
            # Velocity = velocity + acceleration * dt
            F[3:6, 6:9] = np.eye(3) * dt
        return F

    def _get_process_noise_covariance(self, dt: float, q: float) -> np.ndarray:
        """
        Process noise covariance matrix for constant acceleration model.
        q: process noise intensity
        """
        Q = np.eye(self.state_size)
        dt2 = dt * dt
        dt3 = dt2 * dt
        dt4 = dt3 * dt

        if self.params.use_constant_velocity_model:
            # Position noise
            Q[0:3, 0:3] = np.eye(3) * (dt4 / 4.0) * q
            # Cross terms position-velocity
            Q[0:3, 3:6] = np.eye(3) * (dt3 / 2.0) * q
            Q[3:6, 0:3] = Q[0:3, 3:6].T
            # Velocity noise
            Q[3:6, 3:6] = np.eye(3) * dt2 * q
        else:
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
        Returns a tuple with the estimated position and estimated velocity.
        """

        dt = (current_time_millis - self.latest_update_millis) / 1000.0 if self.latest_update_millis is not None else 0.01  # Convert milliseconds to seconds
        dt = min(dt, 10.0) # Clamp dt value to avoid predictions too far in the future

        F = self._get_state_transition_matrix(dt)
        predicted_state = F @ self.state

        return predicted_state[:3], predicted_state[3:6]

    def update(self, measurement: np.ndarray, current_time_millis: int):
        """
        Update step of Kalman filter
        Given a new measurement (position only), update the state and covariance.
        """

        dt = (current_time_millis - self.latest_update_millis) / 1000.0 if self.latest_update_millis is not None else 0.01  # Convert milliseconds to seconds
        self.latest_update_millis = current_time_millis

        # Prediction step
        F = self._get_state_transition_matrix(dt)
        Q = self._get_process_noise_covariance(dt, self.params.process_noise)

        # Apply prediction
        self.state = F @ self.state
        self.P = F @ self.P @ F.T + Q

        # Correction step
        innovation = measurement - self.H @ self.state
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state and covariance
        self.state = self.state + K @ innovation
        self.P = (np.eye(self.state_size) - K @ self.H) @ self.P
