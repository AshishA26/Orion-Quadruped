import pybullet as p
import numpy as np
import time

p.connect(p.GUI)
robotId = p.loadURDF("leg.urdf", [0, 0, 0], useFixedBase=True)

# Link Lengths from URDF
L1, L2, L3 = 0.05, 0.1, 0.1

def my_inverse_kinematics(target_xyz):
    x, y, z = target_xyz
    
    # 1. Coxa Angle
    theta_c = np.atan2(y, x)
    
    # 2. Distance in 2D plane
    r = np.sqrt(x**2 + y**2) - L1
    d = np.sqrt(r**2 + z**2)
    
    # 3. Law of Cosines for Femur/Tibia
    # (Simplified for a specific orientation)
    a1 = np.atan2(z, r)
    a2 = np.acos((L2**2 + d**2 - L3**2) / (2 * L2 * d))
    theta_f = a1 + a2
    
    theta_t = -np.acos((L2**2 + L3**2 - d**2) / (2 * L2 * L3))
    
    return theta_c, theta_f, theta_t

# Loop to test
for i in range(1000):
    # Move target in a circle
    target = [0.12, 0.05 * np.sin(i*0.05), -0.1]
    
    angles = my_inverse_kinematics(target)
    
    # Apply YOUR calculated angles to the URDF
    p.setJointMotorControl2(robotId, 0, p.POSITION_CONTROL, angles[0])
    p.setJointMotorControl2(robotId, 1, p.POSITION_CONTROL, angles[1])
    p.setJointMotorControl2(robotId, 2, p.POSITION_CONTROL, angles[2])
    
    p.stepSimulation()
    time.sleep(0.01)