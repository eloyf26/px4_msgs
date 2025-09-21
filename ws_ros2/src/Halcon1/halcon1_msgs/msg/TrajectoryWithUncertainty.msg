# Predicted trajectory with uncertainty bounds
std_msgs/Header header

# Time points for trajectory (seconds from now)
float64[] times

# Mean trajectory (most likely path)
float64[] mean_x
float64[] mean_y
float64[] mean_z

# Upper confidence bound (mean + 2*sigma)
float64[] upper_x
float64[] upper_y
float64[] upper_z

# Lower confidence bound (mean - 2*sigma)
float64[] lower_x
float64[] lower_y
float64[] lower_z

# Confidence level (e.g., 0.95 for 95% confidence)
float64 confidence_level