# PX4 Build Fix Instructions

The PX4 build error you encountered indicates corrupted build cache and missing submodules. Here's how to fix it:

## Solution Steps

### 1. Clean Build Directory
```bash
cd ~/drone_ws/PX4-Autopilot
rm -rf build
```

### 2. Update Submodules
```bash
cd ~/drone_ws/PX4-Autopilot
git submodule update --init --recursive
```

### 3. Rebuild PX4
```bash
cd ~/drone_ws/PX4-Autopilot
make px4_sitl gz_x500
```

## Alternative: Full Repository Reset (if above doesn't work)

```bash
cd ~/drone_ws
rm -rf PX4-Autopilot

# Clone fresh
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot
git checkout v1.14.0  # Or your preferred stable version
make px4_sitl gz_x500
```

## Common Issues & Solutions

### Missing Tools/check_submodules.sh
- **Cause**: Submodules not initialized
- **Fix**: Run `git submodule update --init --recursive`

### CMakeCache.txt Directory Mismatch
- **Cause**: Build directory moved or corrupted
- **Fix**: Delete build folder and rebuild

### Permission Errors
- **Fix**: Run `sudo chown -R $USER:$USER ~/drone_ws/PX4-Autopilot`

## Verification
After fixing, you should see:
- Gazebo window opens with X500 drone
- PX4 console shows `pxh>` prompt
- No build errors

## For Halcon1 Testing
Once PX4 is running, continue with the 3-terminal setup:
1. Terminal 1: PX4 SITL (this terminal)
2. Terminal 2: MicroXRCE Agent
3. Terminal 3: Halcon1 pipeline