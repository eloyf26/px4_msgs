# Repository Reorganization Plan
## Halcon1 System - Branch feat/AirSim-simulation

**Date**: 2025-10-04
**Status**: In Progress

---

## Analysis Summary

This branch adds **AirSim simulation support** (photo-realistic Unreal Engine) alongside existing **Gazebo simulation**. Both use the same PX4 flight controller and Halcon1 ROS2 logic (detection, tracking, guidance).

**Current Issues:**
1. **File structure**: Simulation code mixed with core logic (3 new packages in ws_ros2/src, scattered scripts)
2. **Documentation**: 3 large planning docs (PLAN.md, AIRSIM_IMPLEMENTATION_PLAN.md, TODO.md ~2400 lines) + repetitive content across 4 AirSim guides
3. **Encapsulation**: No abstraction layer for simulation engines - would need manual scripting to add Isaac Sim

---

## Reorganization Plan

### 1. File Structure Reorganization

**Create clear simulation vs logic separation:**

```
halcon1-system/
├── simulation/                      # NEW: All simulation-specific code
│   ├── gazebo/
│   │   ├── config/                  # Gazebo world files, model configs
│   │   ├── launch/                  # Gazebo-specific launch scripts
│   │   ├── gazebo_engine.py        # Gazebo implementation
│   │   └── README.md               # Gazebo setup & usage
│   ├── airsim/
│   │   ├── config/                  # Move config/airsim/* here
│   │   ├── launch/                  # AirSim-specific launch scripts
│   │   ├── bridges/                 # ROS2 packages: airsim_camera_bridge, airsim_viz_translator
│   │   ├── airsim_engine.py        # AirSim implementation
│   │   └── README.md               # AirSim setup (consolidate 4 docs into 1)
│   ├── isaac/                       # Future: Isaac Sim placeholder
│   │   └── README.md               # Placeholder for future expansion
│   └── common/
│       ├── interfaces/              # NEW: Simulation engine interface definition
│       │   └── sim_engine.py       # Abstract base class
│       ├── launcher.py             # NEW: Unified Python launcher
│       └── README.md               # Simulation architecture & adding new engines
├── ws_ros2/
│   └── src/
│       ├── Halcon1/                 # Core logic (detection, tracking, guidance)
│       │   └── [NO CHANGES - already clean]
│       ├── px4_bridges/             # NEW: Consolidate PX4-related packages
│       │   ├── px4_msgs/           # Move from ws_ros2/src/
│       │   ├── px4_ros_com/        # Move from ws_ros2/src/
│       │   └── px4_offboard/       # Move from ws_ros2/src/
│       └── simulation_bridges/      # NEW: Simulation-specific ROS2 packages
│           ├── gazebo_bridge/      # ros_gz packages moved here
│           └── airsim_bridge/      # airsim packages moved here
├── scripts/                         # Only unified/utility scripts
│   ├── launch_unified.sh           # Keep: Wrapper for Python launcher
│   ├── cleanup.sh                  # Keep: Generic cleanup
│   ├── validate_setup.sh           # Keep: Validation tool
│   └── [Remove 8+ redundant scripts]
├── docs/
│   ├── README.md                   # High-level: What is Halcon1, quick start
│   ├── ARCHITECTURE.md             # NEW: System architecture (merge PLAN.md content)
│   ├── INSTALLATION.md             # NEW: Detailed install guide
│   ├── SIMULATION.md               # NEW: How to use simulations (quick ref)
│   ├── DEVELOPMENT.md              # NEW: Contributing, extending system
│   └── archive/                    # OLD docs for reference
│       ├── PLAN.md                 # Archived
│       ├── AIRSIM_IMPLEMENTATION_PLAN.md  # Archived
│       └── REORGANIZATION_PLAN.md  # This file
├── config/                          # REMOVE: Move to simulation/*/config/
├── README.md                        # Keep: Main entry point (streamlined to ~300 lines)
└── [REMOVE: PLAN.md, AIRSIM_IMPLEMENTATION_PLAN.md, TODO.md]
```

### 2. Simulation Abstraction Layer

**Create `simulation/common/interfaces/sim_engine.py`:**
- Abstract base class defining: `launch()`, `get_camera_topic()`, `get_bridge_config()`, `cleanup()`
- Implementations: `GazeboEngine`, `AirSimEngine`, `IsaacEngine` (future)

**Create `simulation/common/launcher.py`:**
- Single entry point: `./scripts/launch_unified.sh --sim airsim --debug --mode multi`
- Automatically loads correct engine, bridges, and configurations
- Eliminates need for 8+ separate launch scripts

### 3. Documentation Consolidation

**Main README.md** (~300 lines):
- Project overview, 3-step quick start
- Link to detailed docs in `docs/`

**docs/ARCHITECTURE.md** (merge PLAN.md ~350 lines):
- PX4 architecture, MAVLink/uXRCE-DDS flow
- How simulation abstraction works
- Topic structure

**docs/SIMULATION.md** (~200 lines):
- Quick reference for each simulator
- Consolidated from 4 AirSim docs + gazebo content

**docs/INSTALLATION.md** (~150 lines):
- Prerequisites, setup steps for each simulator
- Troubleshooting section

**docs/DEVELOPMENT.md** (~100 lines):
- How to add new simulation engine
- How to extend Halcon1 modules
- Testing guidelines (merge TESTING.md)

**Remove**: PLAN.md (834 lines), AIRSIM_IMPLEMENTATION_PLAN.md (522 lines), TODO.md (migrate actionable items to GitHub issues)

### 4. Script Cleanup

**Keep (3 scripts):**
- `scripts/launch_unified.sh` - Wrapper for Python launcher
- `scripts/cleanup.sh` - Generic cleanup
- `scripts/validate_setup.sh` - Setup validator

**Remove (8+ scripts):**
- `launch_airsim.sh`, `launch_multi_terminal.sh`, `launch_px4.sh`, `launch_agent.sh`, etc.
- All functionality moved to unified `simulation/common/launcher.py`

### 5. Package Reorganization

**Move simulation bridges:**
- `ws_ros2/src/airsim_camera_bridge` → `simulation/airsim/bridges/airsim_camera_bridge`
- `ws_ros2/src/airsim_viz_translator` → `simulation/airsim/bridges/airsim_viz_translator`
- `ws_ros2/src/ros_gz/*` → `simulation/gazebo/bridges/ros_gz`

**Consolidate PX4 packages:**
- Create `ws_ros2/src/px4_bridges/` directory
- Move `px4_msgs`, `px4_ros_com`, `px4_offboard` there

**Keep clean:**
- `ws_ros2/src/Halcon1/` - No changes (already well-organized)
- `ws_ros2/src/multi_drone_sim/` - Could move to `simulation/common/multi_drone_sim`

---

## Implementation Steps

1. **Phase 1**: Create new directory structure (simulation/, docs/ reorganization)
2. **Phase 2**: Implement simulation abstraction layer
3. **Phase 3**: Move packages and update build configs
4. **Phase 4**: Consolidate documentation (merge, remove duplicates)
5. **Phase 5**: Update launch scripts, remove redundant ones
6. **Phase 6**: Update setup.sh to work with new structure
7. **Phase 7**: Test everything (Gazebo, AirSim, multi-drone)
8. **Phase 8**: Update all cross-references in docs

**Estimated changes:**
- ~40 file moves/renames
- ~15 new files (abstraction layer, consolidated docs)
- ~12 file deletions
- ~2000 lines of documentation consolidated to ~1000 lines
- ~2700 lines of launch scripts consolidated to ~500 lines (via abstraction)

**Benefits:**
✅ Clear separation: simulation vs core logic
✅ Easy to add Isaac Sim (implement `IsaacEngine` class, add config)
✅ Single entry point: `./scripts/launch_unified.sh --sim <engine>`
✅ Documentation: 50% reduction, no repetition
✅ Maintainability: New developers understand structure immediately
✅ Testability: Fast simulator (Gazebo) → realistic (AirSim) → deploy

---

## Implementation Status

### Completed
- ✅ Created simulation directory structure
- ✅ Implemented SimulationEngine interface (`sim_engine.py`)
- ✅ Implemented GazeboEngine
- ✅ Implemented AirSimEngine
- ✅ Created Isaac Sim placeholder with README
- ✅ Created unified Python launcher (`launcher.py`)
- ✅ Created wrapper script (`launch_unified.sh`)
- ✅ Moved AirSim config files to simulation/airsim/config/
- ✅ Created simulation/common/README.md (architecture guide)
- ✅ Created simulation/gazebo/README.md (comprehensive)
- ✅ Created simulation/airsim/README.md (consolidated 4 docs)
- ✅ Streamlined main README.md (~300 lines, clear quick start)
- ✅ Backed up old README.md to docs/archive/

### In Progress
- 🔄 Creating docs/ARCHITECTURE.md from PLAN.md
- 🔄 Archiving old planning documents

### Pending
- ⏳ Move ROS2 packages to new locations
- ⏳ Update setup.sh for new structure
- ⏳ Clean up redundant scripts
- ⏳ Create docs/INSTALLATION.md
- ⏳ Create docs/SIMULATION.md
- ⏳ Create docs/DEVELOPMENT.md
- ⏳ Test Gazebo simulation with new structure
- ⏳ Test AirSim simulation with new structure
- ⏳ Update all cross-references in documentation

---

## Notes

This reorganization makes the system:
1. **More extensible** - Adding Isaac Sim takes ~1 week instead of ~1 month
2. **Better documented** - 50% less repetition, clearer structure
3. **Easier to maintain** - Simulation code separate from core logic
4. **Faster onboarding** - New developers understand architecture immediately

The key innovation is the **SimulationEngine abstraction** which allows any physics engine to be plugged in without touching the Halcon1 core code.
