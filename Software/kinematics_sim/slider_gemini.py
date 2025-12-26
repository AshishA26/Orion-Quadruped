import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons

# ==========================================
# 1. Configuration & Robot Dimensions
# ==========================================
# Lengths in arbitrary units (e.g., cm or mm)
L1 = 5.0   # Hip offset (distance from body center to hip rotation axis)
L2 = 12.0  # Femur length (Upper leg)
L3 = 12.0  # Tibia length (Lower leg)

# Joint Limits (in degrees)
LIMITS = {
    'hip_roll': (-45, 45),
    'hip_pitch': (-90, 90),
    'knee_pitch': (-150, 0)
}

# ==========================================
# 2. Kinematics Class
# ==========================================
class LegKinematics:
    def __init__(self, l1, l2, l3):
        self.l1 = l1
        self.l2 = l2
        self.l3 = l3

    def forward_kinematics(self, theta1, theta2, theta3):
        """
        Calculates (x, y, z) from joint angles.
        theta1: Hip Roll (Abduction/Adduction)
        theta2: Hip Pitch (Femur angle)
        theta3: Knee Pitch (Tibia angle relative to femur)
        Angles are in Radians.
        """
        # 1. Hip Roll Rotation (Rotation around X-axis)
        # The joint itself is offset by L1
        # Frame 0 is body, Frame 1 is after hip roll
        
        # 2. Hip Pitch & Knee Pitch (Standard planar 2-link IK in Y-Z plane projected)
        # Calculate the leg projection in the vertical plane defined by theta1
        
        # Effective Length of the leg in the 2D plane (femur + tibia)
        # Using basic trigonometry for serial chain
        
        # Coords relative to the hip attachment point (before roll)
        # We model this as:
        # 1. Rotate for Hip Roll
        # 2. Calculate planar position of Femur and Tibia
        
        s1, c1 = np.sin(theta1), np.cos(theta1)
        s2, c2 = np.sin(theta2), np.cos(theta2)
        s23, c23 = np.sin(theta2 + theta3), np.cos(theta2 + theta3)

        # Position of the knee
        p_knee_local_y = -self.l2 * s2
        p_knee_local_z = -self.l2 * c2
        
        # Position of the foot relative to hip joint center (in the vertical plane)
        p_foot_local_y = -(self.l2 * s2 + self.l3 * s23)
        p_foot_local_z = -(self.l2 * c2 + self.l3 * c23)

        # Apply Hip Roll (Rotation around X-axis)
        # We assume the leg sticks out to the side (Y-axis) or down (Z-axis). 
        # Standard quadruped: Hip axis is X. 
        # The L1 link pushes the start of the leg out in Y.
        
        # Origin (0,0,0) is the hip servo attachment to body.
        # Joint 1 (Roll) is at (0,0,0).
        # Joint 2 (Pitch) is at (0, L1*c1, L1*s1) if L1 rotates? 
        # Usually L1 is a fixed offset *after* the roll servo, or the roll servo *is* the offset.
        # Let's assume: Roll Servo -> L1 linkage -> Pitch Servo -> Femur
        
        # Hip Joint (Start of Femur)
        hip_pos = np.array([0, self.l1 * c1, self.l1 * s1])
        
        # Knee Pos (apply roll rotation to planar y,z)
        # Planar coords: y is horizontal dist from axis, z is vertical
        knee_y_rot = p_knee_local_y * c1 - p_knee_local_z * s1 # This rotation matrix depends on definition
        knee_z_rot = p_knee_local_y * s1 + p_knee_local_z * c1
        
        # Actually, simpler approach:
        # The plane of the leg is rotated by theta1 around X.
        # In that plane:
        #   y_plane = L2*sin(theta2) + L3*sin(theta2+theta3)  (forward/back) -> X axis in global?
        #   z_plane = -L2*cos(theta2) - L3*cos(theta2+theta3) (up/down)
        
        # Let's stick to a standard definition:
        # X: Forward, Y: Left, Z: Up
        
        # Knee Position relative to Hip Pitch Joint
        xk = -self.l2 * np.sin(theta2) 
        zk = -self.l2 * np.cos(theta2)
        
        # Foot Position relative to Hip Pitch Joint
        xf = -(self.l2 * np.sin(theta2) + self.l3 * np.sin(theta2 + theta3))
        zf = -(self.l2 * np.cos(theta2) + self.l3 * np.cos(theta2 + theta3))
        
        # Now apply Hip Roll (Theta1) which rotates the (Y, Z) plane?
        # Usually Hip Roll tilts the leg plane sideways.
        # Hip offset L1 is along the Y axis (rotated by theta1).
        
        # Final Coordinates:
        # x is purely driven by the pitch angles (assuming hip roll axis is along x)
        x = xf 
        
        # y and z are affected by roll
        # The 'depth' of the leg in the rotated plane is 0 if ideal, but actually the leg hangs 'down' in Zf.
        # Distance from roll axis = L1 + (some component if leg swings sideways?)
        # Let's assume standard configuration:
        # 1. Roll rotates the pitch-joint center.
        # 2. Pitch operates in the new vertical plane.
        
        y = (self.l1 + zf * np.sin(theta1)) # Approximation for visual logic
        # Correct 3D Rotation Matrix for Hip Roll (Rot X):
        # [1, 0, 0]
        # [0, c1, -s1]
        # [0, s1, c1]
        
        # Vector in leg plane (at theta1=0): [xf, L1, zf]
        # Rotated:
        y = self.l1 * c1 - zf * s1
        z = self.l1 * s1 + zf * c1
        
        return np.array([x, y, z])

    def inverse_kinematics(self, x, y, z):
        """
        Calculates joint angles from (x, y, z).
        """
        # 1. Hip Roll (Theta 1)
        # The distance from origin to target in Y-Z plane must account for L1
        # Project vector onto Y-Z plane. 
        # Hypotenuse of leg projection = sqrt(y^2 + z^2 - L1^2) is hard.
        # Standard approach:
        
        dyz = np.sqrt(y**2 + z**2)
        if dyz < self.l1:
            return None # Target inside the body thickness (impossible)
            
        # Angle to vector
        alpha = np.arctan2(z, y)
        # Angle offset due to L1
        beta = np.arccos(self.l1 / dyz) if self.l1 <= dyz else 0
        
        # Depending on configuration (knees inward vs outward), sign changes.
        # Assuming knees outward:
        theta1 = alpha + beta # or alpha - beta
        # Let's try simple geometric derivation for theta 1
        # We want to rotate the Y-Z vector so L1 is horizontal? No.
        # We simply want to align the leg plane.
        theta1 = np.arctan2(y, -z) # Simple approximation if L1 is small/ignored, but let's do real IK
        
        # Robust theta1:
        # The leg plane must pass through the target point. The joint is offset by L1.
        # h = sqrt(y^2 + z^2 - l1^2) # Length of leg in the plane (vertical projection)
        # theta1 = atan2(y, -z) ... actually let's stick to the visual sim logic:
        # If we simplify that the hip roll just rotates the plane:
        theta1 = 0 # Placeholder for simple logic if sliders are easier
        # Real calculation:
        L_eff = np.sqrt(y**2 + z**2 - self.l1**2)
        theta1 = np.arctan2(z, y) + np.arctan2(L_eff, self.l1) - np.pi/2

        # 2. Knee & Hip Pitch (Theta 2, Theta 3)
        # Transform (x, y, z) into the 2D plane of the leg
        # Rotated coordinates
        # The 'depth' in the plane corresponds to Z_eff
        
        # Coordinate in leg plane:
        x_eff = x
        z_eff = -np.sqrt(x**2 + y**2 + z**2 - self.l1**2 - x**2) # Vertical distance in leg plane
        # Wait, simpler:
        z_eff = -np.sqrt(L_eff**2) # Distance from hip joint to foot in the plane
        
        # Distance from hip servo to foot
        d = np.sqrt(x_eff**2 + z_eff**2)
        
        # Law of Cosines for Knee (Theta 3)
        # d^2 = l2^2 + l3^2 - 2*l2*l3*cos(pi - theta3)
        cos_theta3 = (d**2 - self.l2**2 - self.l3**2) / (2 * self.l2 * self.l3)
        cos_theta3 = np.clip(cos_theta3, -1.0, 1.0)
        theta3 = -np.arccos(cos_theta3) # Negative for "knee backward" config

        # Calculate Hip Pitch (Theta 2)
        # Angle of vector to foot
        phi = np.arctan2(z_eff, x_eff) # -pi to pi
        # Angle of triangle inside
        beta_tri = np.arccos((self.l2**2 + d**2 - self.l3**2) / (2 * self.l2 * d))
        
        theta2 = phi + beta_tri # Check signs based on config
        
        # Adjust theta2 to be relative to vertical or horizontal as needed
        # In our FK: 0 is straight down? No, 0 is horizontal usually. 
        # FK: z = -l2*c2. If theta2=0, z=-l2. So 0 is straight down.
        # In FK above: x = -l2*sin(theta2). 
        # My IK trig assumes 0 is horizontal x-axis. 
        # Shift:
        theta2 = theta2 + np.pi/2 

        return theta1, theta2, theta3
    
    def parallel_servo_mapping(self, theta_hip, theta_knee):
        """
        Converts theoretical leg angles to actual servo angles 
        for a parallel linkage mechanism.
        
        In a parallel leg:
        Servo A controls the Femur directly.
        Servo B controls the Tibia via a linkage.
        Usually, Servo B angle = Theta_Femur + Theta_Tibia (relative to ground)
        
        Returns: (servo_angle_A, servo_angle_B)
        """
        servo_femur = theta_hip
        # If the second servo is grounded to the body, moving the femur 
        # naturally moves the tibia relative to the femur even if Servo B is still.
        # Therefore, we often need to subtract/add the hip angle.
        servo_tibia = theta_knee + theta_hip 
        return servo_femur, servo_tibia

# ==========================================
# 3. Visualization Setup
# ==========================================
def run_simulation():
    # Initialize Leg
    leg = LegKinematics(L1, L2, L3)

    # Initial Angles (Radians)
    init_th1 = 0.0
    init_th2 = np.radians(30)
    init_th3 = np.radians(-60)

    # Calculate initial position
    init_pos = leg.forward_kinematics(init_th1, init_th2, init_th3)

    # Setup Plot
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    plt.subplots_adjust(left=0.1, bottom=0.35)

    # Plot Elements
    line, = ax.plot([], [], [], 'o-', lw=4, markersize=8, color='teal')
    tip_dot, = ax.plot([], [], [], 'o', color='red') # Foot tip
    
    # Floor reference
    xx, yy = np.meshgrid(np.linspace(-20, 20, 10), np.linspace(-20, 20, 10))
    ax.plot_surface(xx, yy, -20*np.ones_like(xx), alpha=0.1, color='gray')

    # Axis Limits
    ax.set_xlim3d([-25, 25])
    ax.set_ylim3d([-10, 25])
    ax.set_zlim3d([-25, 10])
    ax.set_xlabel('X (Forward)')
    ax.set_ylabel('Y (Side)')
    ax.set_zlabel('Z (Up)')
    ax.set_title("Robot Dog Leg Kinematics Simulator")

    # ==========================================
    # 4. UI Controls (Sliders)
    # ==========================================
    
    # Mode Switch
    rax = plt.axes([0.05, 0.85, 0.15, 0.1])
    radio = RadioButtons(rax, ('FK (Joints)', 'IK (Position)'))

    # Slider Axes
    ax_th1 = plt.axes([0.2, 0.2, 0.65, 0.03])
    ax_th2 = plt.axes([0.2, 0.15, 0.65, 0.03])
    ax_th3 = plt.axes([0.2, 0.1, 0.65, 0.03])
    
    ax_x = plt.axes([0.2, 0.2, 0.65, 0.03])
    ax_y = plt.axes([0.2, 0.15, 0.65, 0.03])
    ax_z = plt.axes([0.2, 0.1, 0.65, 0.03])

    # Create Sliders (Angles in Degrees)
    s_th1 = Slider(ax_th1, 'Hip Roll', -45, 45, valinit=np.degrees(init_th1))
    s_th2 = Slider(ax_th2, 'Hip Pitch', -90, 90, valinit=np.degrees(init_th2))
    s_th3 = Slider(ax_th3, 'Knee Pitch', -150, 0, valinit=np.degrees(init_th3))

    # Create Sliders (Position) - Initially hidden
    s_x = Slider(ax_x, 'X Pos', -20, 20, valinit=init_pos[0])
    s_y = Slider(ax_y, 'Y Pos', 0, 20, valinit=init_pos[1])
    s_z = Slider(ax_z, 'Z Pos', -25, -5, valinit=init_pos[2])

    # Text output for Parallel Mapping
    txt_info = plt.figtext(0.5, 0.02, "", ha="center", fontsize=10, bbox={"facecolor":"orange", "alpha":0.2, "pad":5})

    def toggle_mode(label):
        if label == 'FK (Joints)':
            # Show Angle Sliders, Hide Pos Sliders
            ax_th1.set_visible(True)
            ax_th2.set_visible(True)
            ax_th3.set_visible(True)
            ax_x.set_visible(False)
            ax_y.set_visible(False)
            ax_z.set_visible(False)
            update_fk(None)
        else:
            # Show Pos Sliders, Hide Angle Sliders
            ax_th1.set_visible(False)
            ax_th2.set_visible(False)
            ax_th3.set_visible(False)
            ax_x.set_visible(True)
            ax_y.set_visible(True)
            ax_z.set_visible(True)
            # Sync IK sliders to current FK position before switching
            current_angles = [np.radians(s_th1.val), np.radians(s_th2.val), np.radians(s_th3.val)]
            pos = leg.forward_kinematics(*current_angles)
            s_x.set_val(pos[0])
            s_y.set_val(pos[1])
            s_z.set_val(pos[2])
            update_ik(None)
        fig.canvas.draw_idle()

    radio.on_clicked(toggle_mode)

    # Initial state: FK mode
    ax_x.set_visible(False)
    ax_y.set_visible(False)
    ax_z.set_visible(False)

    def draw_leg(th1, th2, th3):
        # Calculate key points for visualization
        # 1. Body Center (Fixed)
        p0 = np.array([0, 0, 0])
        
        # 2. Hip Roll End (Start of Hip Pitch)
        # Rotated L1 offset
        s1, c1 = np.sin(th1), np.cos(th1)
        p1 = np.array([0, L1 * c1, L1 * s1]) # Rotated Y-axis offset
        # Note: Visualizing L1 is tricky because it rotates. 
        # Let's simplify: The joint axis is X. The link L1 moves in Y-Z plane.
        
        # 3. Knee Position
        # Use FK logic but stop at knee
        s2, c2 = np.sin(th2), np.cos(th2)
        # Knee in planar coords
        ky = -L2 * s2
        kz = -L2 * c2
        # Rotate by Hip Roll
        p2_y = p1[1] + (ky * c1 - kz * s1) # Add to p1? No, p1 is the origin of the pitch rotation.
        p2_z = p1[2] + (ky * s1 + kz * c1)
        p2_x = 0 # If pitch is 0. Wait, Pitch rotates around Y-axis relative to L1?
        # Standard: Pitch rotates around axis perpendicular to femur.
        # Let's use the exact FK math from the class to get points:
        
        # Re-using math for consistency:
        # Foot:
        pf = leg.forward_kinematics(th1, th2, th3)
        
        # Knee (same math as FK but set L3=0)
        temp_leg = LegKinematics(L1, L2, 0)
        pk = temp_leg.forward_kinematics(th1, th2, 0)
        
        # Hip Joint (same math but L2=0, L3=0)
        ph = temp_leg.forward_kinematics(th1, 0, 0) # Wait, this gives us L1 offset?
        # Actually easier:
        ph = np.array([0, L1*np.cos(th1), L1*np.sin(th1)]) # Correct hip pitch center
        
        xs = [p0[0], ph[0], pk[0], pf[0]]
        ys = [p0[1], ph[1], pk[1], pf[1]]
        zs = [p0[2], ph[2], pk[2], pf[2]]
        
        line.set_data(xs, ys)
        line.set_3d_properties(zs)
        
        # Info Box: Parallel Servo Angles
        s_femur, s_tibia = leg.parallel_servo_mapping(th2, th3)
        txt_info.set_text(
            f"Virtual Angles | Roll: {np.degrees(th1):.1f}° | Pitch: {np.degrees(th2):.1f}° | Knee: {np.degrees(th3):.1f}°\n"
            f"Parallel Servo Map | Hip Servo: {np.degrees(s_femur):.1f}° | Knee Servo: {np.degrees(s_tibia):.1f}°"
        )

    def update_fk(val):
        th1 = np.radians(s_th1.val)
        th2 = np.radians(s_th2.val)
        th3 = np.radians(s_th3.val)
        draw_leg(th1, th2, th3)
        fig.canvas.draw_idle()

    def update_ik(val):
        x = s_x.val
        y = s_y.val
        z = s_z.val
        
        angles = leg.inverse_kinematics(x, y, z)
        
        if angles:
            th1, th2, th3 = angles
            draw_leg(th1, th2, th3)
        else:
            txt_info.set_text("Target Unreachable!")
            
        fig.canvas.draw_idle()

    # Bind sliders
    s_th1.on_changed(update_fk)
    s_th2.on_changed(update_fk)
    s_th3.on_changed(update_th3_wrapper := lambda v: update_fk(v))
    
    s_x.on_changed(update_ik)
    s_y.on_changed(update_ik)
    s_z.on_changed(update_ik)

    # Initial Draw
    draw_leg(init_th1, init_th2, init_th3)
    plt.show()

if __name__ == "__main__":
    run_simulation()