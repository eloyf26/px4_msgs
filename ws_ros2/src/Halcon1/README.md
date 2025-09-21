
# Halcon I Software

The Halcon I Software is composed of four independent modules with clearly defined interfaces.

* Drone Detection (drone_detection): Using YOLO detect the position of the enemy drone based on the camera position.
    - Input: Camera feed
    - Output: Relative Position of enemy drone
* Position Tracker (position_tracker): Tracks the position of the Halcon I and transform relative coordinates to absolute coordinates respect to the origin (starting point).
    - Input: Visual Odometry (GPS-denied) and/or GPS
    - Output: Absolute positions of the Halcon I and enemy drone
* Trajectory Predictor (trajectory_predictor): Estimates the current trajectory of the enemy drone based on noisy measurements, and predicts future trajectory.
    - Input: Stream of absolute positions of the enemy drone.
    - Output: Future absolute trajectory prediction.
* Interceptor (interceptor): Generates an interception trajectory for the Halcon I to follow based on the enemy drone trajectory.
    - Input: Trajectory prediction of the enemy drone.
    - Output: Interception trajectory (in absolute coordinates)


The output of each module plugs into the input of the next module. The input of the first module is the camera feed, and the output of the last module needs to be fed to the PX4 flight controller.