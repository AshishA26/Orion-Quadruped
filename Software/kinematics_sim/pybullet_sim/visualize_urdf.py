import pybullet as p
import pybullet_data
import time

# Connect to the GUI
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.81)

# Load a floor and your robot
p.loadURDF("plane.urdf")
# Ensure 'leg.urdf' is in the same folder
robotId = p.loadURDF("leg.urdf", [0, 0, 0.3], useFixedBase=True)

# Create sliders for each joint
num_joints = p.getNumJoints(robotId)
user_params = []

for i in range(num_joints):
    joint_info = p.getJointInfo(robotId, i)
    joint_name = joint_info[1].decode("utf-8")
    # Add a slider: p.addUserDebugParameter(name, min, max, start_val)
    slider = p.addUserDebugParameter(joint_name, -3.14, 3.14, 0)
    user_params.append(slider)

print("\n--- Debugger Ready ---")
print("Move the sliders in the 'Parameters' window to test joint rotations.")

try:
    while True:
        # Read sliders and update robot joints
        for i in range(num_joints):
            target_pos = p.readUserDebugParameter(user_params[i])
            p.setJointMotorControl2(robotId, i, p.POSITION_CONTROL, target_pos)
        
        p.stepSimulation()
        time.sleep(0.01)
except KeyboardInterrupt:
    p.disconnect()