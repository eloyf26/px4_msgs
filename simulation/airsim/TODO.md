# AirSim TODO

## ✅ Architecture Integration - COMPLETE (2025-10-05)

The AirSim simulation has been successfully integrated with the engine template system!

### Current State (COMPLETE):
```
simulation/common/debug/
└── ally_visualizer/    ✅ DONE - Used by both Gazebo and AirSim

simulation/airsim/debug/
├── camera_bridge/      ✅ DONE - Publishes /camera/image
└── enemy_visualizer/   ✅ DONE - AirSim-specific implementation
```

### Completed Tasks:
1. [x] Create `simulation/airsim/debug/enemy_visualizer/` package
   - Queries AirSim API for enemy ground truth: `airsim_client.getMultirotorState("Enemy")`
   - SUBTRACTS ally spawn offset (opposite of Gazebo which adds offset)
   - Publishes to `/debug/enemy/*` topics
   - Full ROS2 package with proper structure

2. [x] Update `simulation/airsim/engine.py`
   - Uses `ally_visualizer` (shared with Gazebo)
   - Launches `enemy_visualizer` for multi-drone mode
   - Passes ally offset as ROS2 parameters

3. [x] Create dynamic settings.json generation
   - Templates: `settings_template_single.json` and `settings_template_multi.json`
   - Drone positions flow through `DroneConfig` like Gazebo
   - Settings generated at runtime from templates

4. [ ] Delete `simulation/airsim/debug/viz_translator/` package
   - **Pending** - Delete after confirming enemy_visualizer works in testing

5. [ ] Test with AirSim multi-drone simulation
   - **Pending** - User will test

### Key Differences from Gazebo:
- **Gazebo**: Both PX4s report local (0,0,0), enemy visualizer ADDS offset
- **AirSim**: AirSim API returns global position, enemy visualizer SUBTRACTS ally offset

### Priority:
**COMPLETE** - AirSim now fully integrated with engine template system ✅

### Documentation:
- Implementation details: `simulation/airsim/AIRSIM_INTEGRATION_COMPLETE.md`
- Gazebo reference: `simulation/gazebo/debug/enemy_visualizer/`
- Old AirSim code: `simulation/airsim/debug/viz_translator/` (to be deleted)

---

## Future Enhancements (Optional)

### Low Priority:
- [ ] Add support for more AirSim features (depth camera, segmentation)
- [ ] CLI arguments for custom drone positions: `--ally-pos x,y,z`
- [ ] Support for >2 drones in simulation
- [ ] Weather/time-of-day parameter handling in templates
