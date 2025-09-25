### MILESTONE 1: Convention 1-2 Oct --> Demo in Gazebo

Right now everything is ready so that you can forget about ROS2 and just implement algorithms / models in python. Mock implementations in the following modules must be replaced with actual algorithms:

- detection_algorithm.py --> YOLO based drone detection.
- coordinate_transformer.py --> 1st draft is a very simple calculation that estimates depth based on width / height of the drone bbox and converts camera coordinates to world coordinates using a basic pinhole model.
- kalman_filter.py and monte_carlo.py --> Implement actual Kalman Filter and actual Monte Carlo prediction (an initial draft is present in the old Halcon1 repo).
- trajectory_planner.py --> Implement some method for interception trajectory (MCP, PN, ...).

### MILESTONE 2: ...