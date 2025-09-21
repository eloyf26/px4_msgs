# Enemy drone pose in world coordinates (NED frame)
std_msgs/Header header

# Position in NED frame (meters)
float64 x
float64 y
float64 z

# Velocity in NED frame (m/s)
float64 vx
float64 vy
float64 vz

# Covariance matrix (6x6 flattened)
# Order: x, y, z, vx, vy, vz
float64[36] covariance