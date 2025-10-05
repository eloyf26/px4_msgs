#!/usr/bin/env python3
"""Test script to debug AirSim coordinate system"""

import airsim

# Connect to AirSim
client = airsim.MultirotorClient()
client.confirmConnection()
print("Connected to AirSim\n")

# Get Ally position
print("=== ALLY DRONE ===")
ally_pose = client.simGetObjectPose("Ally")
print(f"simGetObjectPose: X={ally_pose.position.x_val:.3f}, Y={ally_pose.position.y_val:.3f}, Z={ally_pose.position.z_val:.3f}")

ally_state = client.getMultirotorState(vehicle_name="Ally")
ally_kinematics = ally_state.kinematics_estimated
print(f"getMultirotorState: X={ally_kinematics.position.x_val:.3f}, Y={ally_kinematics.position.y_val:.3f}, Z={ally_kinematics.position.z_val:.3f}")

# Get Enemy position
print("\n=== ENEMY DRONE ===")
enemy_pose = client.simGetObjectPose("Enemy")
print(f"simGetObjectPose: X={enemy_pose.position.x_val:.3f}, Y={enemy_pose.position.y_val:.3f}, Z={enemy_pose.position.z_val:.3f}")

enemy_state = client.getMultirotorState(vehicle_name="Enemy")
enemy_kinematics = enemy_state.kinematics_estimated
print(f"getMultirotorState: X={enemy_kinematics.position.x_val:.3f}, Y={enemy_kinematics.position.y_val:.3f}, Z={enemy_kinematics.position.z_val:.3f}")

# Calculate relative position
print("\n=== RELATIVE POSITION (Enemy - Ally) ===")
rel_x = enemy_pose.position.x_val - ally_pose.position.x_val
rel_y = enemy_pose.position.y_val - ally_pose.position.y_val
rel_z = enemy_pose.position.z_val - ally_pose.position.z_val
print(f"Enemy relative to Ally (NED): X={rel_x:.3f}, Y={rel_y:.3f}, Z={rel_z:.3f}")

# Apply NED to ENU conversion (current implementation)
print("\n=== COORDINATE CONVERSION (Current) ===")
print(f"NED input: [{rel_x:.3f}, {rel_y:.3f}, {rel_z:.3f}]")
enu_x = rel_y  # East = NED Y
enu_y = rel_x  # North = NED X
enu_z = -rel_z # Up = -NED Z
print(f"ENU output: X={enu_x:.3f}, Y={enu_y:.3f}, Z={enu_z:.3f}")
print(f"  → In RViz this means: {enu_x:.1f}m East, {enu_y:.1f}m North, {enu_z:.1f}m Up")

# Expected from settings.json: Enemy at (5, 0, 0) NED
print("\n=== EXPECTED ===")
print("Settings.json: Ally=(0,0,0), Enemy=(5,0,0) in NED")
print("Expected: Enemy 5m North of Ally")
print("Expected in RViz (ENU): X=0 (East), Y=5 (North), Z=0 (Up)")
