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