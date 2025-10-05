import numpy as np

from algorithms.pro_nav import ProportionalNavigation, ProportionalNavigationParameters
from algorithms.kalman_filter import KalmanFilter, KalmanFilterParameters


class StateManager:
    """
    Keeps track of the drone position and speed, as well as enemy position and speed (both timestamped). Functionalities:

    1. Can update it's state variables when it receives an update_friendly or update_enemy call.
    2. Runs Kalman Filter to get an estimate of the enemy position and speed.
    3. Runs Proportional Navigation to get the required acceleration to intercept the enemy.
    4. Can provide at any time `t` the desired acceleration.
    """

    def __init__(self, kf_params: KalmanFilterParameters, pn_params: ProportionalNavigationParameters,
                 interception_range: float, offset_m: float = 0.0):

        self.kf_filter = KalmanFilter(kf_params)
        self.pro_nav = ProportionalNavigation(pn_params)

        self.interception_range = interception_range # Distance at which we consider the enemy intercepted and stop accelerating
        self.offset = offset_m # Applies offset in meters to the z coordinate of the enemy position to avoid actual collision
                               # during testing. Positive values means the enemy is considered to be higher than it actually is.

        self.friendly_position = None
        self.friendly_velocity = None
        self.friendly_last_update = None

        self.enemy_last_update = None


    def update_friendly(self, friendly_position: np.ndarray, friendly_velocity: np.ndarray, current_time_millis: int):
        self.friendly_position = friendly_position
        self.friendly_velocity = friendly_velocity
        self.friendly_last_update = current_time_millis

    def update_enemy(self, enemy_position: np.ndarray, current_time_millis: int):
        self.enemy_last_update = current_time_millis

        # Update Kalman Filter with new enemy position
        self.kf_filter.update(enemy_position, current_time_millis)

    def update(self, current_time_millis: int):
        # Predict enemy state with Kalman Filter
        enemy_estimated_position, enemy_estimated_velocity = self.kf_filter.predict(current_time_millis)
        friendly_estimated_position, friendly_estimated_velocity = self._predict_friendly_state(current_time_millis)

        # If any of them are None, we cannot compute acceleration
        if friendly_estimated_position is None or friendly_estimated_velocity is None or enemy_estimated_position is None or enemy_estimated_velocity is None:
            return None

        # Apply offset to enemy position
        enemy_estimated_position[2] += self.offset

        # Check if we are already within interception range
        distance_to_enemy = np.linalg.norm(friendly_estimated_position - enemy_estimated_position)
        if distance_to_enemy < self.interception_range:
            return np.zeros(3) # TODO: We want to actually display something here right?

        # Now use ProNav to compute required acceleration
        required_acceleration = self.pro_nav.compute_acceleration(
            friendly_position=friendly_estimated_position,
            friendly_velocity=friendly_estimated_velocity,
            enemy_position=enemy_estimated_position,
            enemy_velocity=enemy_estimated_velocity
        )

        return required_acceleration

    def _predict_friendly_state(self, current_time_millis: int):
        if self.friendly_position is None or self.friendly_velocity is None or self.friendly_last_update is None:
            return None, None

        dt = (current_time_millis - self.friendly_last_update) / 1000.0  # Convert milliseconds to seconds
        predicted_position = self.friendly_position + self.friendly_velocity * dt
        return predicted_position, self.friendly_velocity