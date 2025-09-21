import numpy as np
from halcon1_detection.enemy_drone_simulator import EnemyDroneSimulator

class DetectionAlgorithm:
    def __init__(self):
        self.enemy_sim = EnemyDroneSimulator()
        self.camera_width = 640
        self.camera_height = 480

    def detect(self, friendly_position=None, friendly_quaternion=None, current_time_sec=0):
        # Default friendly position at origin if not provided
        if friendly_position is None:
            friendly_position = np.array([0.0, 0.0, 0.0])

        # Get enemy world position using simulation time
        enemy_pos = self.enemy_sim.get_world_position(current_time_sec)

        # Project to camera pixels
        x, y, confidence = self.enemy_sim.project_to_camera(
            enemy_pos, friendly_position, friendly_quaternion
        )

        return x, y, confidence