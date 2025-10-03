### MILESTONE 1: Convention 1-2 Oct --> Demo in Gazebo

Right now everything is ready so that you can forget about ROS2 and just implement algorithms / models in python. Mock implementations in the following modules must be replaced with actual algorithms:

- [x] detection_algorithm.py --> YOLO based drone detection.
- [x] coordinate_transformer.py --> 1st draft is a very simple calculation that estimates depth based on width / height of the drone bbox and converts camera coordinates to world coordinates using a basic pinhole model.
- [x] guidance (state_manager.py) --> Basic Kalman Filter + Proportional Navigation implementation.

### MILESTONE 2: ...

Generic Improvmenets
- [ ] Guidance
  - [x] Add process noise to Kalman Filter
  - [ ] Proportional navigation
    - [ ] Agile drone movement (feels clunky right now)
    - [ ] Directional acceleration aim at future drone position (not current)
    - [ ] Fine-tune ProNav parameters

### PHASE 1: AirSim Simulation Support

**Goal**: Add AirSim as alternative simulation environment (no Halcon1 ROS2 code changes)

#### Documentation & Planning
- [x] Create PLAN.md with complete architecture documentation
- [x] Document PX4 simulation architecture (Gazebo, AirSim, Real Hardware)
- [x] Document MAVLink + uXRCE-DDS + ROS2 data flow

#### AirSim Setup
- [x] Create AirSim configuration (config/airsim/settings.json)
  - [x] PX4Multirotor vehicle type
  - [x] LockStep mode enabled
  - [x] Camera matching Gazebo specs (640x480, 60° FOV)
- [x] Create AirSim launch script (scripts/launch_airsim.sh)
- [x] Update README.md with AirSim instructions

#### Installation & Testing (Pending)
- [ ] Install AirSim prebuilt environment
  - [ ] Download Blocks environment
  - [ ] Test SimpleFlight baseline
- [ ] Install airsim_ros_pkgs
  - [ ] Clone repository
  - [ ] Build for ROS2 Humble
  - [ ] Fix compatibility issues if needed
- [ ] Test PX4 ↔ AirSim connection
  - [ ] Verify MAVLink connection on TCP 4560
  - [ ] Test arm and takeoff
- [ ] Test camera bridge
  - [ ] Verify /camera/image topic
  - [ ] Check image quality and frame rate
- [ ] Test full Halcon1 pipeline
  - [ ] Detection working
  - [ ] Tracking publishing poses
  - [ ] Guidance sending commands
- [ ] Validation
  - [ ] Run interception scenario
  - [ ] Compare with Gazebo performance
  - [ ] Document results

### PHASE 2: Advanced Navigation (monocular-slam-drone integration)

**Goal**: Add depth estimation, 3D mapping, and obstacle avoidance

#### New Modules (from monocular-slam-drone)
- [ ] halcon1_depth_estimation
  - [ ] Port Depth Anything V2 to ROS2
  - [ ] Input: /camera/image
  - [ ] Output: /depth/map
- [ ] halcon1_mapping
  - [ ] Port VoxArray 3D occupancy grid to ROS2
  - [ ] Port numba-optimized raycasting
  - [ ] Input: /depth/map + drone pose
  - [ ] Output: /occupancy/occupied, /occupancy/empty
- [ ] halcon1_navigation
  - [ ] Port A* 3D path planning to ROS2
  - [ ] Input: current pose, goal, occupancy grid
  - [ ] Output: /navigation/planned_path
- [ ] Integration with guidance
  - [ ] Modify guidance to respect obstacle-free paths
  - [ ] Combine interception with collision avoidance

#### Testing
- [ ] Test in complex AirSim environments
  - [ ] Buildings environment
  - [ ] City environment
- [ ] Validate obstacle avoidance during interception

### Productionize

- [ ] Guidance
  - [ ] Kalman Filter for drone trajectory (can't assume constant acceleration).
  - [ ] Advanced alternative to ProNav (i.e. MCP).
  - [ ] Use more data (i.e. enemy / friendly drone orientation)
- [ ] Detection
  - [ ] Multiple drones
  - [ ] Obstacle avoidance (→ Phase 2)
- [ ] Position tracker
  - [ ] GPS-denied visual odometry (i.e. ORB-SLAM3) (→ Phase 2 mapping)
- [ ] Safety
  - [ ] Abort system
  - [ ] Detonation system