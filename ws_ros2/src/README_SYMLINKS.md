# Understanding Symlinks in ws_ros2/src/

## What are Symlinks?

**Symlinks (symbolic links)** are like shortcuts or pointers to directories/files located elsewhere on your filesystem.

When you see this in `ls -la`:
```
lrwxrwxrwx ... ally_visualizer -> /home/.../Halcon1/debug/ally_visualizer
```

- The `l` at the start means it's a symlink
- `ally_visualizer` is the symlink name (what you see in `src/`)
- `->` shows where it points
- The actual files live at `/home/.../Halcon1/debug/ally_visualizer`

## Why Use Symlinks?

**ROS2's `colcon build` requires all packages to be in `ws_ros2/src/`**

But we organize code logically:
- Real-system packages → `ws_ros2/src/Halcon1/`
- Simulation packages → `simulation/*/debug/`

**Solution:** Symlinks let packages appear in `src/` while living elsewhere.

## Current Symlinks

All symlinks are organized in `ws_ros2/src/symlinks/` for clarity:

```bash
ws_ros2/src/symlinks/
├── halcon1_debug/
│   └── ally_visualizer → ../../Halcon1/debug/ally_visualizer
├── gazebo_debug/
│   └── enemy_visualizer → ../../../../simulation/gazebo/debug/enemy_visualizer
├── common_debug/
│   └── enemy_control → ../../../../simulation/common/debug/enemy_control
├── airsim_debug/
│   ├── camera_bridge → ../../../../simulation/airsim/debug/camera_bridge
│   └── viz_translator → ../../../../simulation/airsim/debug/viz_translator
└── bridges/
    └── ros_gz → ../../../../simulation/gazebo/bridges
```

## How to Check Symlinks

```bash
# List all symlinks organized by category
tree -L 2 ws_ros2/src/symlinks/

# Check where a specific symlink points
file ws_ros2/src/symlinks/halcon1_debug/ally_visualizer

# Or use readlink
readlink ws_ros2/src/symlinks/gazebo_debug/enemy_visualizer
```

## Are They Active?

**Yes!** If you see `->` in the `ls -la` output, they're active.

`colcon build` follows symlinks automatically - it builds packages as if they were real directories.

## Do I Need to Delete Them?

**No!** Symlinks are intentional. They're listed in `.gitignore` so git doesn't track them.

If a symlink is broken (points to non-existent location):
```bash
# Example: broken symlink
ls -la ws_ros2/src/ally_visualizer
# Shows red/blinking in many terminals

# Fix by recreating
rm ws_ros2/src/ally_visualizer
ln -sf /actual/path/to/ally_visualizer ws_ros2/src/ally_visualizer
```

## Creating New Symlinks

When adding a new package outside `src/`, organize it in the appropriate subdirectory:

```bash
# From ws_ros2/src/symlinks/
cd ws_ros2/src/symlinks/

# For Halcon1 debug tools
ln -sf ../../Halcon1/debug/new_tool halcon1_debug/new_tool

# For Gazebo-specific
ln -sf ../../../../simulation/gazebo/debug/new_tool gazebo_debug/new_tool

# For AirSim-specific
ln -sf ../../../../simulation/airsim/debug/new_tool airsim_debug/new_tool

# For common simulation debug
ln -sf ../../../../simulation/common/debug/new_tool common_debug/new_tool
```

**Important:** Use relative paths from `symlinks/` directory for portability.

## Structure Benefits

This structure keeps code organized by purpose:

```
ws_ros2/src/
├── Halcon1/              # Real drone system
│   ├── modules/          # Core functionality
│   ├── debug/            # Debug tools (work with real hardware)
│   └── msgs/
└── (symlinks to simulation packages)

simulation/
├── common/debug/         # Shared simulation debug
├── gazebo/debug/         # Gazebo-specific debug
└── airsim/debug/         # AirSim-specific debug
```

Everything in `Halcon1/` can run on **real hardware**.
Everything in `simulation/` is **simulation-only**.
