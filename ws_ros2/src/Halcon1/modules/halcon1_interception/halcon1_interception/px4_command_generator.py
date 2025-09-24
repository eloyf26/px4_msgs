import numpy as np
from dataclasses import dataclass
from px4_msgs.msg import TrajectorySetpoint
from halcon1_types import TimestampedTrajectory, DronePose

@dataclass
class InterceptionTrajectory:
    setpoints: list[TrajectorySetpoint]
    is_active: bool
    init_timestamp: float

class PX4CommandGenerator:
    def __init__(self):
        pass

    @staticmethod
    def generate_single_point(timestamp: float, position: DronePose) -> TrajectorySetpoint:
        setpoint = TrajectorySetpoint()
        setpoint.timestamp = int(timestamp * 1e6)  # Convert to microseconds for PX4

        # Position (NED frame)
        setpoint.position = [float(position.x), float(position.y), float(position.z)]

        # Velocity and acceleration (set to NaN for position control)
        setpoint.velocity = [float('nan')] * 3
        setpoint.acceleration = [float('nan')] * 3

        # Yaw (face forward)
        setpoint.yaw = float('nan')  # Let PX4 handle yaw
        setpoint.yawspeed = float('nan')

        return setpoint

    @staticmethod
    def generate_interception_trajectory(timestamped_trajectory: TimestampedTrajectory,
                                       init_timestamp: float) -> InterceptionTrajectory:
        """Convert TimestampedTrajectory to InterceptionTrajectory with PX4 TrajectorySetpoints"""
        setpoints = []

        for timestamp, position in zip(timestamped_trajectory.timestamps, timestamped_trajectory.positions):
            setpoint = PX4CommandGenerator.generate_single_point(timestamp, position)
            setpoints.append(setpoint)

        return InterceptionTrajectory(
            setpoints=setpoints,
            is_active=True,
            init_timestamp=init_timestamp
        )

    @staticmethod
    def generate_current_setpoint(interception_trajectory: InterceptionTrajectory,
                                current_time: float,
                                friendly_pose: DronePose) -> TrajectorySetpoint:
        """Generate current trajectory setpoint based on time and friendly pose"""
        if not interception_trajectory.is_active or len(interception_trajectory.setpoints) == 0:
            # Return hover setpoint at current position
            setpoint = PX4CommandGenerator.generate_single_point(current_time, friendly_pose)
            return setpoint

        # Calculate elapsed time since trajectory started
        elapsed_time = current_time - interception_trajectory.init_timestamp

        # Find appropriate setpoint based on elapsed time
        target_setpoint = None
        for setpoint in interception_trajectory.setpoints:
            setpoint_time = (setpoint.timestamp / 1e6) - interception_trajectory.init_timestamp
            if setpoint_time >= elapsed_time:
                target_setpoint = setpoint
                break

        # If past all setpoints, use the last one
        if target_setpoint is None:
            target_setpoint = interception_trajectory.setpoints[-1]

        # Update timestamp to current time
        current_setpoint = TrajectorySetpoint()
        current_setpoint.timestamp = int(current_time * 1e6)
        current_setpoint.position = target_setpoint.position
        current_setpoint.velocity = target_setpoint.velocity
        current_setpoint.acceleration = target_setpoint.acceleration
        current_setpoint.yaw = target_setpoint.yaw
        current_setpoint.yawspeed = target_setpoint.yawspeed

        return current_setpoint

    @staticmethod
    def is_trajectory_complete(interception_trajectory: InterceptionTrajectory,
                              current_time: float) -> bool:
        """Check if trajectory is complete"""
        if not interception_trajectory.is_active or len(interception_trajectory.setpoints) == 0:
            return True

        # Get last setpoint time
        last_setpoint = interception_trajectory.setpoints[-1]
        last_setpoint_time = last_setpoint.timestamp / 1e6

        return current_time >= last_setpoint_time