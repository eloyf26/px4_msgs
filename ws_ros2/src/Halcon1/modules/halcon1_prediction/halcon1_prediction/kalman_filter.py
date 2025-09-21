import numpy as np

class KalmanFilter:
    def __init__(self, dt=0.1):
        # State: [x, y, z, vx, vy, vz]
        self.state = np.zeros(6)
        self.P = np.eye(6) * 100.0  # Initial covariance

        # State transition matrix (constant velocity model)
        self.dt = dt
        self.F = np.array([
            [1, 0, 0, dt, 0, 0],
            [0, 1, 0, 0, dt, 0],
            [0, 0, 1, 0, 0, dt],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])

        # Process noise
        q = 0.1  # Process noise intensity
        self.Q = np.array([
            [dt**3/3, 0, 0, dt**2/2, 0, 0],
            [0, dt**3/3, 0, 0, dt**2/2, 0],
            [0, 0, dt**3/3, 0, 0, dt**2/2],
            [dt**2/2, 0, 0, dt, 0, 0],
            [0, dt**2/2, 0, 0, dt, 0],
            [0, 0, dt**2/2, 0, 0, dt]
        ]) * q

        # Measurement matrix (we measure position and velocity)
        self.H = np.eye(6)

        # Measurement noise
        self.R = np.diag([1.0, 1.0, 1.0, 2.0, 2.0, 2.0])

        self.initialized = False

    def predict(self):
        """Predict step of Kalman filter"""
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.state, self.P

    def update(self, measurement, measurement_covariance=None):
        """Update step of Kalman filter"""
        if not self.initialized:
            # Initialize state with first measurement
            self.state = measurement[:6]
            if measurement_covariance is not None:
                self.P = measurement_covariance
            self.initialized = True
            return self.state, self.P

        # Use provided covariance or default
        R = measurement_covariance if measurement_covariance is not None else self.R

        # Kalman gain
        S = self.H @ self.P @ self.H.T + R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Update state
        y = measurement - self.H @ self.state
        self.state = self.state + K @ y

        # Update covariance
        I = np.eye(6)
        self.P = (I - K @ self.H) @ self.P

        return self.state, self.P

    def get_state_and_covariance(self):
        """Get current state estimate and covariance"""
        return self.state.copy(), self.P.copy()