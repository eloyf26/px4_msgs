# Interactive World Selection - Implementation Complete ✅

**Date:** 2025-10-05
**Feature:** Interactive world/environment selection in `launch_simulator()`

## Summary

Removed `--world` CLI parameter and implemented interactive world selection directly in each engine's `launch_simulator()` method. This provides a cleaner, more user-friendly interface.

## Changes Made

### 1. **Removed --world from CLI** ✅

**Files Modified:**
- `simulation/common/interfaces/sim_engine.py` - Removed `world` from `SimulationConfig`
- `simulation/common/launcher.py` - Removed `--world` argument and world validation logic

**Impact:**
- Simpler CLI: `./scripts/launch.sh --sim airsim --mode multi --debug`
- No need to remember world names beforehand
- World selection happens interactively when you start the system

### 2. **AirSim: Interactive Selection + Auto-Launch** ✅

**File:** `simulation/airsim/engine.py`

**Added `_prompt_world_selection()` method:**
- Shows numbered list of available environments
- Shows installation status for each (✓ installed / ✗ not installed)
- Accepts numeric input or Enter for default
- Validates selection is actually installed
- Returns selected world name

**Updated `launch_simulator()`:**
- Calls `_prompt_world_selection()` first
- **Auto-launches AirSim binary in new terminal** (no more manual step!)
- Waits 10 seconds for Unreal Engine to initialize
- Auto-verifies connection with 30-second timeout
- Tracks AirSim process for cleanup

**User Experience:**
```
[AirSim] Available environments:
  1. blocks (default) [✓ installed]
  2. landscape [✓ installed]
  3. city [✗ not installed]

[AirSim] Select environment (1-3, or Enter for default): [Enter]

[AirSim] Selected environment: blocks
[AirSim] Launching AirSim...
[AirSim] ✓ AirSim launched in new terminal
[AirSim] Waiting for Unreal Engine to initialize...
[AirSim] Connecting to AirSim API...
[AirSim] ✓ Successfully connected to AirSim
```

### 3. **Gazebo: Interactive Selection** ✅

**File:** `simulation/gazebo/engine.py`

**Added `_prompt_world_selection()` method:**
- Shows numbered list of 12 available worlds
- Accepts numeric input or Enter for default
- Returns selected world name

**Updated `launch_simulator()`:**
- Calls `_prompt_world_selection()` and stores result in `self.selected_world`
- Gazebo still launched by PX4 (architecture unchanged)

**Updated `get_px4_env_vars()`:**
- Uses `self.selected_world` instead of `self.config.world`
- Falls back to default if not set

**User Experience:**
```
[Gazebo Harmonic] Available worlds:
  1. default (default)
  2. baylands
  3. forest
  4. lawn
  5. windy
  ...

[Gazebo Harmonic] Select world (1-12, or Enter for default): [Enter]

[Gazebo Harmonic] Selected world: default
[Gazebo Harmonic] Gazebo will be launched by PX4
```

## Before vs After

### Before (with --world):
```bash
./scripts/launch.sh --simulator airsim --world blocks --mode multi --debug

# Manual step required:
[AirSim] IMPORTANT: Manual step required
[AirSim] Please launch AirSim environment manually:
[AirSim]   1. Open a new terminal
[AirSim]   2. cd /home/user/AirSimEnvironments/.../LinuxNoEditor
[AirSim]   3. ./Blocks.sh
[AirSim] Press ENTER when AirSim is running...
```

### After (interactive):
```bash
./scripts/launch.sh --simulator airsim --mode multi --debug

[AirSim] Available environments:
  1. blocks (default) [✓ installed]
  2. landscape [✓ installed]
Select: [Enter]

[AirSim] ✓ AirSim launched automatically
[AirSim] ✓ Connected to AirSim
# Everything automatic!
```

## Benefits

✅ **Cleaner CLI** - Fewer arguments to remember
✅ **User-friendly** - See available options before choosing
✅ **Validation** - Only allows selection of installed environments
✅ **Automatic** - AirSim now auto-launches (like Gazebo)
✅ **Consistent** - Both engines work the same way
✅ **Flexible** - Easy to add more worlds/environments

## Implementation Details

### AirSim Installation Check

The interactive prompt shows which environments are installed:

```python
env_path = Path.home() / "AirSimEnvironments" / dir_name / "LinuxNoEditor"
script_path = env_path / script
is_installed = env_path.exists() and script_path.exists()
```

If user selects a non-installed environment, they get an error message and can choose again.

### Auto-Launch Process

**AirSim:**
1. Launch binary in new terminal with blue header
2. Wait 10 seconds for Unreal Engine startup
3. Poll AirSim API for 30 seconds until connection succeeds
4. If fails, show error and check terminal for issues

**Gazebo:**
- No change - PX4 still launches Gazebo automatically
- World selection stored and passed to PX4 via environment variables

### Process Tracking

AirSim process is now tracked in `self.processes` for automatic cleanup:
```python
self.processes.append(("airsim_simulator", proc))
```

When you Ctrl+C the launcher, AirSim terminal window closes automatically.

## Backward Compatibility

**Breaking Change:** `--world` parameter removed
**Migration:** Remove `--world` from any scripts/aliases
**Impact:** Users must interact with prompts (can't be fully automated)

**Future Enhancement:** Could add environment variable override:
```bash
AIRSIM_WORLD=landscape ./scripts/launch.sh --sim airsim
# Skips interactive prompt, uses env var value
```

## Files Modified

1. `simulation/common/interfaces/sim_engine.py` - Removed world from SimulationConfig
2. `simulation/common/launcher.py` - Removed --world argument and validation
3. `simulation/airsim/engine.py` - Added interactive selection + auto-launch
4. `simulation/gazebo/engine.py` - Added interactive selection

## Testing

```bash
# Test Gazebo
./scripts/launch.sh --sim gazebo
# Should show world selection menu

# Test AirSim
./scripts/launch.sh --sim airsim --mode multi --debug
# Should show environment selection, then auto-launch

# Test with Enter (default)
# Should select default world without typing

# Test with number
# Should select corresponding world
```

## Future Enhancements

- [ ] Add environment variable override to skip prompts (for automation)
- [ ] Show world descriptions in selection menu
- [ ] Cache last-used world and offer as default
- [ ] Add keyboard arrows for selection (not just numbers)
- [ ] Show world thumbnails in terminal (if supported)

## Summary

Interactive world selection makes the system more user-friendly and consistent across engines. AirSim now auto-launches like Gazebo, removing the manual step entirely. The CLI is simpler with fewer arguments to remember.

**Result:** Cleaner interface, better UX, fully automated! 🚁
