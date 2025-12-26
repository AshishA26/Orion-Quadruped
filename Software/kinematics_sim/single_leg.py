import matplotlib.pyplot as plt
import numpy as np

def plot_leg(coxa_angle, femur_angle, tibia_angle, l1=0.05, l2=0.1, l3=0.1):
    """
    Visualizes a single 3-DOF leg.
    Angles are in degrees. 
    L1, L2, L3 are lengths of Coxa, Femur, and Tibia.
    """
    # Convert angles to radians
    rad_c = np.radians(coxa_angle)
    rad_f = np.radians(femur_angle)
    rad_t = np.radians(tibia_angle)

    # Calculate Joint Positions (Forward Kinematics)
    # Joint 0: Origin (Base of Coxa)
    j0 = np.array([0, 0, 0])

    # Joint 1: End of Coxa (Rotation around Z)
    j1 = np.array([l1 * np.cos(rad_c), 
                   l1 * np.sin(rad_c), 
                   0])

    # Joint 2: End of Femur
    # The femur moves in the plane defined by the coxa angle
    j2 = j1 + np.array([l2 * np.cos(rad_f) * np.cos(rad_c),
                        l2 * np.cos(rad_f) * np.sin(rad_c),
                        l2 * np.sin(rad_f)])

    # Joint 3: End of Tibia (The Foot / End Effector)
    # Tibia angle is usually relative to the femur
    j3 = j2 + np.array([l3 * np.cos(rad_f + rad_t) * np.cos(rad_c),
                        l3 * np.cos(rad_f + rad_t) * np.sin(rad_c),
                        l3 * np.sin(rad_f + rad_t)])

    # Prepare data for plotting
    nodes = np.array([j0, j1, j2, j3])
    x, y, z = nodes[:, 0], nodes[:, 1], nodes[:, 2]

    # Plotting
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot segments (bones)
    ax.plot(x, y, z, '-o', linewidth=4, markersize=8, color='#2c3e50', label='Leg Linkage')
    
    # Highlight the Foot
    ax.scatter(x[-1], y[-1], z[-1], color='red', s=100, label='Foot (End Effector)')

    # Set plot limits (adjust based on your leg lengths)
    limit = (l1 + l2 + l3)
    ax.set_xlim([-limit, limit])
    ax.set_ylim([-limit, limit])
    ax.set_zlim([-limit, limit])

    ax.set_xlabel('X (Forward)')
    ax.set_ylabel('Y (Side)')
    ax.set_zlabel('Z (Up/Down)')
    ax.set_title(f'Leg Visualization\nCoxa:{coxa_angle}°, Femur:{femur_angle}°, Tibia:{tibia_angle}°')
    ax.legend()
    
    plt.show()

# Example: Plotting a leg partially bent
# Change these angles to see how your linkage moves!
plot_leg(coxa_angle=15, femur_angle=-30, tibia_angle=-60)