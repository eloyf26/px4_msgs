import numpy as np

class KalmanFilter:
    def __init__(self):
        # State: [x, y, z, vx, vy, vz]
        self.state = np.zeros(6)
        self.P = np.eye(6) * 100.0  # Initial covariance

        # State transition matrix (constant velocity model)
        self.dt = 0.1  # 10Hz update rate
        self.F = np.array([
            [1, 0, 0, self.dt, 0, 0],
            [0, 1, 0, 0, self.dt, 0],
            [0, 0, 1, 0, 0, self.dt],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])

        # Process noise
        self.Q = np.eye(6) * 0.1

        # Measurement matrix (we only measure position)
        self.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0]
        ])

        # Measurement noise
        self.R = np.eye(3) * 1.0

        self.initialized = False

    def predict(self):
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, measurement):
        if not self.initialized:
            # Initialize state with first measurement
            self.state[0] = measurement[0]
            self.state[1] = measurement[1]
            self.state[2] = measurement[2]
            self.initialized = True
            return

        # Kalman gain
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Update state
        y = measurement - self.H @ self.state
        self.state = self.state + K @ y

        # Update covariance
        I = np.eye(6)
        self.P = (I - K @ self.H) @ self.P

    def get_state(self):
        return self.state.copy()


class TrackingAlgorithm:
    def __init__(self):
        self.kalman = KalmanFilter()
        self.focal_length = 500.0  # pixels
        self.assumed_depth = 10.0  # meters

    def pixel_to_3d(self, pixel_x, pixel_y):
        # Simple pinhole camera model
        # Assume fixed depth for simplicity
        cx = 320  # camera center x
        cy = 240  # camera center y

        x = (pixel_x - cx) * self.assumed_depth / self.focal_length
        y = (pixel_y - cy) * self.assumed_depth / self.focal_length
        z = self.assumed_depth

        return np.array([x, y, z])

    def process_detection(self, pixel_x, pixel_y):
        # Convert to 3D
        position_3d = self.pixel_to_3d(pixel_x, pixel_y)

        # Predict
        self.kalman.predict()

        # Update with measurement
        self.kalman.update(position_3d)

        # Get filtered state
        state = self.kalman.get_state()

        return {
            'x': state[0],
            'y': state[1],
            'z': state[2],
            'vx': state[3],
            'vy': state[4],
            'vz': state[5]
        }