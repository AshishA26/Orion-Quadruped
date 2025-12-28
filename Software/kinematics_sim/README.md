# Inverse Kinematics Sim

## Plotting approach

You define the limb lengths (L1​,L2​,L3​) and use your IK equations to calculate joint angles (θ1​,θ2​,θ3​).
You then use Forward Kinematics (FK) to plot the resulting lines.

- `matplotlib_simple_sim`
    - IK sim using matplotlib, assuming knee servo is mounted on femur
    - shows orientation control and choosing center of rotation
    - shows accounting for right vs left leg and 360 degree `atan2`

## PyBullet approach
- You load a URDF file (a 3D model of your robot) and send your IK-calculated angles to the motors.
- It handles gravity and collisions. You'll see if the body drops when the legs move or if the feet slip on the floor.
- `conda install -c conda-forge pybullet`