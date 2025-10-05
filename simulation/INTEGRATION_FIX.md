# AirSim Integration Fix - Module Name Collision

**Date:** 2025-10-05
**Issue:** AirSim engine not recognized by launcher
**Root Cause:** Python module name collision
**Status:** ✅ FIXED

## Problem

When running:
```bash
./scripts/launch.sh --simulator airsim
```

Got error:
```
error: argument --sim/--simulator: invalid choice: 'airsim' (choose from 'gazebo')
```

## Root Cause Analysis

**Python Import Caching Issue:**

The launcher was doing:
```python
sys.path.insert(0, "simulation/gazebo")
import engine as gazebo_engine  # Loads simulation/gazebo/engine.py

sys.path.insert(0, "simulation/airsim")
import engine as airsim_engine  # Python returns CACHED module from gazebo!
```

**Why this happened:**
- Both engines named `engine.py`
- Python caches modules by name, not by path
- Second `import engine` returned the already-loaded Gazebo engine
- AirSim's `SimulationEngineFactory.register_engine()` never executed

**Evidence:**
```python
>>> import engine as airsim_engine
>>> hasattr(airsim_engine, 'AirSimEngine')  # False - it's actually Gazebo!
>>> hasattr(airsim_engine, 'GazeboEngine')  # True
```

## Solution

Used `importlib.util` to load modules by file path with unique module names:

```python
import importlib.util

# Import Gazebo engine
gazebo_engine_path = Path(__file__).parent.parent / "gazebo" / "engine.py"
spec = importlib.util.spec_from_file_location("gazebo_engine_module", gazebo_engine_path)
gazebo_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gazebo_engine)

# Import AirSim engine
airsim_engine_path = Path(__file__).parent.parent / "airsim" / "engine.py"
spec = importlib.util.spec_from_file_location("airsim_engine_module", airsim_engine_path)
airsim_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(airsim_engine)
```

**Benefits:**
- Each module loaded independently
- Unique internal module names prevent caching collision
- Both registration calls execute properly

## Files Modified

- `simulation/common/launcher.py` (lines 33-47)

## Verification

```bash
$ python3 simulation/common/launcher.py --help
Available simulators:
  gazebo, airsim  ✅

$ ./scripts/launch.sh --simulator airsim --mode multi --debug
[Launcher] Using AirSim simulation engine  ✅
[Launcher] Drones: 2
[Launcher] Debug: True
```

## Lessons Learned

1. **Python module caching gotcha**: `import module_name` caches by name, not path
2. **Solution for same-named modules**: Use `importlib.util.spec_from_file_location()`
3. **Give unique internal names**: Even if files have same name, give different module IDs

## Future Recommendations

### Option A: Keep Current Solution ✅
- Works perfectly
- Clear what's happening
- Easy to add more engines

### Option B: Rename Files (Alternative)
```
simulation/gazebo/gazebo_engine.py
simulation/airsim/airsim_engine.py
```
Then use normal imports:
```python
sys.path.insert(0, "simulation/gazebo")
import gazebo_engine

sys.path.insert(0, "simulation/airsim")
import airsim_engine
```

**Recommendation:** Stick with Option A (current fix) - no need to rename files across the codebase.

## Testing Checklist

- [x] Gazebo single drone mode works
- [x] Gazebo multi drone mode works
- [x] AirSim recognized as valid simulator
- [x] AirSim engine loads and initializes
- [ ] AirSim single drone end-to-end (user to test)
- [ ] AirSim multi drone with visualization (user to test)

## Impact

✅ **Zero breaking changes** - Gazebo continues to work
✅ **AirSim now available** - Both engines functional
✅ **Template system ready** - Easy to add future engines
