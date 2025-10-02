### MILESTONE 1: Convention 1-2 Oct --> Demo in Gazebo

Right now everything is ready so that you can forget about ROS2 and just implement algorithms / models in python. Mock implementations in the following modules must be replaced with actual algorithms:

- [ ] detection_algorithm.py --> YOLO based drone detection.
- [ ] coordinate_transformer.py --> 1st draft is a very simple calculation that estimates depth based on width / height of the drone bbox and converts camera coordinates to world coordinates using a basic pinhole model.
- [x] guidance (state_manager.py) --> Basic Kalman Filter + Proportional Navigation implementation.

### MILESTONE 2: ...

Generic Improvmenets
- [ ] Guidance
  - [x] Add process noise to Kalman Filter
  - [ ] Proportional navigation
    - [ ] Agile drone movement (feels clunky right now)
    - [ ] Directional acceleration aim at future drone position (not current)
    - [ ] Fine-tune ProNav parameters

### Productionize

- [ ] Guidance
  - [ ] Kalman Filter for drone trajectory (can't assume constant acceleration).
  - [ ] Advanced alternative to ProNav (i.e. MCP).
  - [ ] Use more data (i.e. enemy / friendly drone orientation)
- [ ] Detection
  - [ ] Multiple drones
  - [ ] Obstacle avoidance
- [ ] Position tracker
  - [ ] GPS-denied visual odometry (i.e. ORB-SLAM3)
- [ ] Safety
  - [ ] Abort system
  - [ ] Detonation system