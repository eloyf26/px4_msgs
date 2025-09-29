import numpy as np
from px4_msgs.msg import TrajectorySetpoint, OffboardControlMode, VehicleCommand

# non-stamped OFFBOARD message template
OFFBOARD_MSG = OffboardControlMode()
OFFBOARD_MSG.position = False
OFFBOARD_MSG.velocity = False
OFFBOARD_MSG.acceleration = True
OFFBOARD_MSG.attitude = False
OFFBOARD_MSG.body_rate = False

# non-stamped TRAJECTORY message template
TRAJECTORY_MSG = TrajectorySetpoint()
TRAJECTORY_MSG.position = [float('nan'), float('nan'), float('nan')]
TRAJECTORY_MSG.velocity = [float('nan'), float('nan'), float('nan')]
TRAJECTORY_MSG.acceleration = [float('nan'), float('nan'), float('nan')]
TRAJECTORY_MSG.jerk = [float('nan'), float('nan'), float('nan')]
TRAJECTORY_MSG.yaw = float('nan')
TRAJECTORY_MSG.yawspeed = float('nan')

# non-stamped VEHICLE COMMAND message template for setting offboard mode
SET_OFFBOARD_MODE_MSG = VehicleCommand()
SET_OFFBOARD_MODE_MSG.command = VehicleCommand.VEHICLE_CMD_DO_SET_MODE
SET_OFFBOARD_MODE_MSG.param1 = 1 # Custom mode
SET_OFFBOARD_MODE_MSG.param2 = 6 # Offboard mode


class PX4CommandGenerator:

    @staticmethod
    def generate_offboard_message(current_time_millis: int):
        """Generate OffboardControlMode message for PX4"""
        OFFBOARD_MSG.timestamp = current_time_millis
        return OFFBOARD_MSG

    @staticmethod
    def generate_trajectory_message(current_acceleration: np.ndarray, current_time_millis: int):
        """Generate TrajectorySetpoint message for PX4 with the acceleration"""
        TRAJECTORY_MSG.acceleration = current_acceleration.tolist()
        TRAJECTORY_MSG.timestamp = current_time_millis
        return TRAJECTORY_MSG

    @staticmethod
    def generate_set_offboard_mode_command(current_time_millis: int):
        """Generate VehicleCommand message to set offboard mode and arm the vehicle"""
        SET_OFFBOARD_MODE_MSG.timestamp = current_time_millis
        return SET_OFFBOARD_MODE_MSG
