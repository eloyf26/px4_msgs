
# Halcon I Software

The Halcon I Software is composed of three independent modules with clearly defined interfaces.

* Drone Detection (drone_detection): Using YOLO detect the position of the enemy drone based on the camera position.
    - Input: Camera feed (sensor_msgs/Image)
    - Output: Relative Position of enemy drone
* Position Tracker (position_tracker): Tracks the position of the Halcon I and transform relative coordinates to absolute coordinates respect to the origin (starting point).
    - Input: Visual Odometry (GPS-denied) and/or GPS (geometry_msgs/PoseStamped)
    - Output: Absolute positions of the Halcon I and enemy drone
* Guidance (guidance): Estimates the current trajectory of the enemy drone based on noisy measurements, and produces output
interception commands for the Halcon I to follow.
    - Input: Stream of absolute positions of the enemy drone and friendly drone.
    - Output: Trajectory setpoints for PX4 flight controller

The interface between modules are ROS2 topics with standard message types, but each module (which are python) has their own
simplified interface for ease of use. The interface types are defined in the `halcon1_types` package. To keep everything
in sync we add a header with timestamps to every message. However, we keep `halcon1_types` and modules timestamp agnostic
to keep algorithms simple (except the guidance node which requires timestamp for correct trajectory generation).

The output of each module plugs into the input of the next module. The input of the first module is the camera feed, and the output of the last module needs to be fed to the PX4 flight controller.