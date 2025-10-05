import numpy as np
from px4_msgs.msg import TrajectorySetpoint, OffboardControlMode, VehicleCommand


class PX4CommandGenerator:

    @staticmethod
    def generate_offboard_message(current_time_micros: int):
        """Generate OffboardControlMode message for PX4"""
        msg = OffboardControlMode()
        msg.position = False
        msg.velocity = False
        msg.acceleration = True
        msg.attitude = False
        msg.body_rate = False
        msg.timestamp = current_time_micros
        return msg

    @staticmethod
    def generate_trajectory_message(current_acceleration: np.ndarray, current_time_micros: int):
        """Generate TrajectorySetpoint message for PX4 with the acceleration"""
        msg = TrajectorySetpoint()
        msg.position = [float('nan'), float('nan'), float('nan')]
        msg.velocity = [float('nan'), float('nan'), float('nan')]
        msg.acceleration = current_acceleration.tolist()
        msg.jerk = [float('nan'), float('nan'), float('nan')]
        msg.yaw = float('nan')
        msg.yawspeed = float('nan')
        msg.timestamp = current_time_micros
        return msg

    @staticmethod
    def generate_set_offboard_mode_command(current_time_micros: int):
        """Generate VehicleCommand message to set offboard mode"""
        msg = VehicleCommand()
        msg.command = VehicleCommand.VEHICLE_CMD_DO_SET_MODE
        msg.param1 = float(1)  # Custom mode
        msg.param2 = float(6)  # Offboard mode
        msg.timestamp = current_time_micros
        return msg
