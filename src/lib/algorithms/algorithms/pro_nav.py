import numpy as np
from dataclasses import dataclass

@dataclass
class ProportionalNavigationParameters:
    # Vehicle-specifics
    max_acceleration: float = 12.0  # Maximum allowable acceleration (m/s²)
    max_velocity: float = 20.0  # Maximum allowable velocity (m/s)

    # Fine-tunable algorithm parameters
    navigation_constant: float = 3.0  # Typical values are between 3 and 5
    directional_to_los_change_scale: float = 40
    directional_to_los_change_threshold: float = 20 # Threshold below which to apply mostly los change acceleration
    max_seconds_look_ahead: float = 5.0  # Max seconds to look ahead for interception prediction

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
        interception_direction = self._compute_interception_direction(relative_position, relative_velocity)
        directional_acceleration = interception_direction * self.params.max_acceleration

        # Step 4: Calculate weights based on distance and velocity
        current_speed = np.linalg.norm(friendly_velocity)
        speed_ratio = current_speed / self.params.max_velocity  # 0 when slow, 1 when at max speed

        # Distance-based weight: 1 when far (>threshold), 0 when close (<threshold)
        distance_weight = (distance - self.params.directional_to_los_change_threshold) / self.params.directional_to_los_change_scale
        distance_weight = np.clip(distance_weight, 0.0, 1.0)

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

    def _compute_interception_direction(self,
                                        relative_position: np.ndarray,
                                        relative_velocity: np.ndarray) -> np.ndarray:
        """
        Compute a lead direction toward the target based on short-term prediction using relative motion.
        Args:
            relative_position: r = target_pos - interceptor_pos  (shape (3,))
            relative_velocity: v_r = target_vel - interceptor_vel (shape (3,))
        Returns:
            unit vector (3,) pointing from interceptor to predicted target position
            using relative motion extrapolation.
        """

        # short-term lead time proportional to distance and closing rate
        r_norm = np.linalg.norm(relative_position)
        v_rel_norm = np.linalg.norm(relative_velocity)

        # avoid division by zero
        t_lead = r_norm / max(v_rel_norm, 1e-3)

        # clamp to maximum look-ahead
        t_lead = min(t_lead, self.params.max_seconds_look_ahead)

        # predicted intercept point relative to interceptor
        intercept_vector = relative_position + relative_velocity * t_lead

        # fallback if zero vector
        norm_intercept = np.linalg.norm(intercept_vector)
        if norm_intercept < 1e-6:
            return np.zeros(3)

        return intercept_vector / norm_intercept