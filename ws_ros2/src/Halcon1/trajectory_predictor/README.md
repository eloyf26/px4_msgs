
## Interface

* **INPUT:** A stream of absolute positions of the enemy drone.
* **OUTPUT:** A stream of predicted absolute trayectories of the enemy drone.

## Implementation details

The module is divided into two parts:

1. **Kalman-Filter** (KF) with constant velocity: Estimates true trajectory of the enemy drone based on the noisy input.
2. **Monte-Carlo** (MC) simulation: Estimates future trajectory of the enemy drone based on estimated true trajectory.

To estimate the optimal trajectory for interception, Monte-Carlo will pick starting points sampling the normal distribution of current drone positions (KF produces an estimation + covariance that can be used to construct a normal distribution).

The final output is the centroid of the MC trajectories (gives the interceptor module the best chance of correcting trajectory on the fly as new predictions arrive).

