import numpy as np

class InterceptionAlgorithm:
    def __init__(self):
        self.friendly_speed = 5.0  # m/s assumed drone speed
        self.update_rate = 50  # Hz for PX4 commands

    def find_interception_point(self, times, x, y, z, friendly_pos=(0, 0, 0)):
        # Find closest reachable point on predicted trajectory
        best_point = None
        min_time_diff = float('inf')

        for i in range(len(times)):
            target_pos = np.array([x[i], y[i], z[i]])
            distance = np.linalg.norm(target_pos - np.array(friendly_pos))
            time_to_reach = distance / self.friendly_speed

            # Check if we can reach this point in time
            if time_to_reach <= times[i]:
                time_diff = abs(time_to_reach - times[i])
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_point = target_pos

        # If no reachable point, go for the first one
        if best_point is None and len(x) > 0:
            best_point = np.array([x[0], y[0], z[0]])

        return best_point

    def generate_waypoints(self, target, current_pos=(0, 0, 0)):
        # Simple direct path to target
        if target is None:
            return None

        # For now, just return the target position
        # In reality, this would generate intermediate waypoints
        return {
            'target_x': target[0],
            'target_y': target[1],
            'target_z': target[2]
        }