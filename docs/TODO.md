### MILESTONE 1: Convention 1-2 Oct --> Demo in Gazebo

Right now everything is ready so that you can forget about ROS2 and just implement algorithms / models in python. Mock implementations in the following modules must be replaced with actual algorithms:

- [x] detection_algorithm.py --> YOLO based drone detection.
- [x] coordinate_transformer.py --> 1st draft is a very simple calculation that estimates depth based on width / height of the drone bbox and converts camera coordinates to world coordinates using a basic pinhole model.
- [x] guidance (state_manager.py) --> Basic Kalman Filter + Proportional Navigation implementation.

# Roadmap to TRL 4 November 7th 2025 (today is 5th november 2025)

Current state: Modules tested individually in the simulation environment successfully.

- 9th Oct: Success in simulation in ideal conditions (no wind, no obstacles, easy target detection, easy target trajectory)
- 18th Oct: Hardware in the loop (HITL) simulation with PX4 SITL and Gazebo (Running ROS2 nodes in Jetson Nano)
- 25th Oct: Tests in outdoor environment with real drones (easy target detection, easy target trajectory)
  - 25th Oct -- Take our software + hardware to the convention and talk with other companies that may provide early detection,
    launching bases, or other useful tech to integrate with us.
- 7th Nov: TRL 4 achieved --> Successful interceptions in ideal conditions is possible.

### MILESTONE 2 (9th October): Success in the simulation

Generic Improvmenets
- [ ] Guidance
  - [x] Add process noise to Kalman Filter
  - [ ] Proportional navigation
    - [x] Agile drone movement (feels clunky right now)
    - [ ] Directional acceleration aim at future drone position (not current)
    - [ ] Fine-tune ProNav parameters
- [ ] Detection
  - [ ] Choose best candidate box taking into account previous box position (not just most confidence)
  - [ ] _(Only if required)_ Fine tune the model
  - [ ] _(Only if required)_ Improve depth estimation algorithm

### MILESTONE 3 (18th October): Hardware in the loop (HITL) simulation with PX4 SITL and Gazebo

- [ ] Run ROS2 nodes in Jetson Nano
- [ ] Connect to PX4 SITL and Gazebo through Micro XRCE-DDS Agent + Camera Bridge

### MILESTONE 4 (25th October): Outdoor tests with real drones

- [ ] Implement safety systems
  - [ ] Abort system
  - [ ] Mock Detonation system
- [ ] Automatize deployment --> One button to launch everything, another button to start the mission.
- [ ] Compile a report with results and lessons learned from testing, and generate plan for MILESTONE 5.

### MILESTONE 5 (7th November): TRL 4 achieved --> Successful interceptions in ideal conditions is possible.



## Productionize

- [ ] Guidance
  - [ ] Advanced alternative to ProNav (i.e. MCP).
  - [ ] Use more data (i.e. enemy / friendly drone orientation)
- [ ] Detection
  - [ ] Multiple drones
  - [ ] Obstacle avoidance
- [ ] Position tracker
  - [ ] GPS-denied visual odometry (i.e. ORB-SLAM3)
