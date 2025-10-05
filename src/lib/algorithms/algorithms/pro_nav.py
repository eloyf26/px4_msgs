import numpy as np
from dataclasses import dataclass

@dataclass
class ProportionalNavigationParameters:
    navigation_constant: float = 3.0  # Typical values are between 3 and 5
    max_acceleration: float = 5.0  # Maximum allowable acceleration (m/s²)
    max_velocity: float = 10.0  # Maximum allowable velocity (m/s)
    directional_to_los_change_threshold: float = 50 # Threshold above which to apply mostly directional acceleration
                                                    # and below which to apply mostly los change acceleration (m)
    full_direction_acceleration: float = 100 # At threshold + full_directional apply fully the directional acceleration

class ProportionalNavigation:

    def __init__(self, params: ProportionalNavigationParameters):
        self.params = params

    def compute_acceleration(self, friendly_position: np.ndarray, friendly_velocity: np.ndarray,
                             enemy_position: np.ndarray, enemy_velocity: np.ndarray) -> np.ndarray:
        """
        Compute the required acceleration for the friendly drone to intercept the enemy drone using Proportional Navigation.

        :param friendly_position: Current position of the friendly drone (3D vector).
        :param friendly_velocity: Current velocity of the friendly drone (3D vector).
        :param enemy_position: Current position of the enemy drone (3D vector).
        :param enemy_velocity: Current velocity of the enemy drone (3D vector).
        :return: Required acceleration for interception (3D vector).
        """

        # Relative position and velocity
        relative_position = enemy_position - friendly_position
        relative_velocity = enemy_velocity - friendly_velocity

        distance = np.linalg.norm(relative_position)

        if distance < 1e-6:
            print(f"[ProNav] Already at target, zero acceleration")
            return np.zeros(3) # Already at target

        # Line of Sight (LOS) unit vector
        los_unit = relative_position / distance
        closing_velocity = -np.dot(relative_velocity, los_unit)

        # Step 1: Calculate LOS rate
        # LOS rate is the component of relative velocity perpendicular to LOS
        relative_velocity_perpendicular = relative_velocity - np.dot(relative_velocity, los_unit) * los_unit

        # Step 2: Apply basic ProNav formula
        # a = N * V_closing * ω_los * direction_perpendicular_to_los
        if np.linalg.norm(relative_velocity_perpendicular) < 1e-6:
            # No perpendicular velocity, so no ProNav acceleration needed
            pronav_acceleration = np.zeros(3)
        else:
            los_rate_magnitude = np.linalg.norm(relative_velocity_perpendicular) / distance

            # Direction should be opposite to the perpendicular velocity to reduce LOS rate
            perpendicular_direction = relative_velocity_perpendicular / np.linalg.norm(relative_velocity_perpendicular)

            # ProNav acceleration magnitude
            acceleration_magnitude = self.params.navigation_constant * abs(closing_velocity) * los_rate_magnitude

            # ProNav acceleration vector
            pronav_acceleration = acceleration_magnitude * perpendicular_direction

        # Step 3: Calculate directional acceleration
        # TODO: This is a simplification, should point in front of the enemy drone, not at the current position of the enemy drone.
        directional_acceleration = (relative_position / distance) * self.params.max_acceleration

        # Step 4: Calculate weights based on distance and velocity
        current_speed = np.linalg.norm(friendly_velocity)
        speed_ratio = current_speed / self.params.max_velocity  # 0 when slow, 1 when at max speed

        # Distance-based weight: 1 when far (>threshold), 0 when close (<threshold)
        if distance > self.params.directional_to_los_change_threshold:
            distance_weight = 1.0
        else:
            distance_weight = 0.0

        # Speed-based weight: 1 when slow, 0 when fast
        speed_weight = 1.0 - speed_ratio

        # Weight for directional acceleration: higher when drone is slow OR far from target
        # Use max to implement OR logic (either condition gives high weight)
        weight_directional = max(speed_weight, distance_weight)

        # Weight for ProNav: higher when drone is fast AND close to target
        weight_pronav = 1.0 - weight_directional

        # Step 5: Combine accelerations
        combined_acceleration = (weight_directional * directional_acceleration +
                               weight_pronav * pronav_acceleration)

        # Step 6: Apply acceleration limits
        acceleration_norm = np.linalg.norm(combined_acceleration)
        if acceleration_norm > self.params.max_acceleration:
            combined_acceleration = combined_acceleration * (self.params.max_acceleration / acceleration_norm)

        return combined_acceleration
