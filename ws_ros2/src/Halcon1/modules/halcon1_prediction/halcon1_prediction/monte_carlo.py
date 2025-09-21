import numpy as np

class MonteCarloPredictor:
    def __init__(self, num_samples=100):
        self.num_samples = num_samples

    def predict_trajectories(self, state, covariance, time_horizon=5.0, dt=0.5):
        """
        Generate Monte Carlo trajectory samples

        Args:
            state: Current state estimate [x, y, z, vx, vy, vz]
            covariance: State covariance matrix (6x6)
            time_horizon: Prediction horizon in seconds
            dt: Time step for predictions

        Returns:
            times: Array of time points
            trajectories: Dict with mean and confidence bounds
        """
        # Time points
        num_steps = int(time_horizon / dt)
        times = np.arange(1, num_steps + 1) * dt

        # Sample initial states from Gaussian distribution
        samples = np.random.multivariate_normal(state, covariance, self.num_samples)

        # Propagate each sample forward in time
        trajectories = np.zeros((self.num_samples, num_steps, 3))

        for i, sample in enumerate(samples):
            pos = sample[:3]
            vel = sample[3:6]

            for t in range(num_steps):
                # Constant velocity model with small noise
                pos = pos + vel * dt
                vel = vel + np.random.normal(0, 0.01, 3)  # Small acceleration noise

                trajectories[i, t, :] = pos

        # Calculate statistics
        mean_trajectory = np.mean(trajectories, axis=0)
        std_trajectory = np.std(trajectories, axis=0)

        # 95% confidence bounds (approximately 2 sigma)
        upper_bound = mean_trajectory + 2 * std_trajectory
        lower_bound = mean_trajectory - 2 * std_trajectory

        return {
            'times': times,
            'mean': mean_trajectory,
            'upper': upper_bound,
            'lower': lower_bound,
            'samples': trajectories  # Keep samples for visualization if needed
        }