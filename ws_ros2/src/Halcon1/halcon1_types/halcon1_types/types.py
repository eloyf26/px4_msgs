from dataclasses import dataclass

@dataclass
class DetectionResult:
    x: int
    y: int
    width: int
    height: int

@dataclass
class DronePose:
    x: float
    y: float
    z: float

@dataclass
class TimestampedTrajectory:
    timestamps: list[float]
    positions: list[DronePose]

"""
NOTE FOR DEVS: If you add a new shard type to this module, it has to be also added to the __all__ list in __init__.py
"""