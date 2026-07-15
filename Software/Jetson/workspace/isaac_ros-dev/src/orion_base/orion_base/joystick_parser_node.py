import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from orion_msgs.msg import OrionMotionCmd
from orion_msgs.msg import OrionEyesCmd
from typing import Tuple

# --- Joystick axis and button mapping (PS5 controller) ---
# NOTE: All settings are in CMD_NORMAL, unless otherwise specified
# NOTE: For PS5 controller, L2 and R2 require msg.axes, not msg.buttons
# LS_HORZ = 0 # Strafe left/right if CMD_NORMAL, change y offset if CMD_EXTRAS
# LS_VERT = 1 # Move forward/backward if CMD_NORMAL, change x offset if CMD_EXTRAS
# RS_HORZ = 2 # Turn left/right
# RS_VERT = 5
# DPAD_VERT = 7 # Pitch if CMD_NORMAL, move pivot point forward/backward if CMD_EXTRAS
# DPAD_HORZ = 6 # Roll if CMD_NORMAL, move pivot point left/right if CMD_EXTRAS
# BTN_SQUARE = 0 # Yaw left if CMD_NORMAL, reset pivot point in CMD_EXTRAS
# BTN_CROSS = 1 # Height (z offset) decrease
# BTN_CIRCLE = 2 # Yaw right
# BTN_TRIANGLE = 3 # Height (z offset) increase
# BTN_L1 = 4 # Deadman switch
# BTN_R1 = 5 # Reset, sets CMD_RESET
# BTN_L2 = 3 # Sets CMD_EYES
# BTN_R2 = 4 # Boost mode (axis 4)
# BTN_SHARE = 8 # Sets CMD_HEEL
# BTN_OPTIONS = 9 # Sets CMD_WAVE
# BTN_L3 = 10 # Sets CMD_DANCE
# BTN_R3 = 11  # Sets CMD_EXTRAS
# BTN_PS = 12
# BTN_TOUCHPAD = 13 # Sets CMD_NORMAL

# --- Joystick axis and button mapping (Fandragon controller) ---
LS_HORZ = 0
LS_VERT = 1 
RS_HORZ = 2
RS_VERT = 3
DPAD_VERT = 5
DPAD_HORZ = 4
BTN_SQUARE = 3 # X
BTN_CROSS = 2 # A
BTN_CIRCLE = 1 # B
BTN_TRIANGLE = 0 # Y
BTN_L1 = 4
BTN_R1 = 5
BTN_L2 = 6
BTN_R2 = 7
BTN_SHARE = 8  # Select
BTN_OPTIONS = 9 # Start
BTN_L3 = 10
BTN_R3 = 11

class JoystickParser(Node):
    def __init__(self):
        super().__init__('joystick_parser_node')
        self.joystick_subscriber = self.create_subscription(Joy, 'joy', self.joy_callback, 10)
        self.motion_publisher = self.create_publisher(OrionMotionCmd, 'joy_motion_cmd', 10)
        self.eyes_publisher = self.create_publisher(OrionEyesCmd, 'joy_eyes_cmd', 10)
        
        # Parameters
        self.declare_parameter('max_speed', 1.0) # Max speed in m/s or rad/s
        self.declare_parameter('max_roll', math.radians(20)) # +/- 20 degrees
        self.declare_parameter('max_pitch', math.radians(25)) # +/- 25 degrees
        self.declare_parameter('max_yaw', math.radians(30)) # +/- 30 degrees
        self.declare_parameter('max_z_offset', 60.0) # Maximum translation up/down in mm
        self.declare_parameter('boost', 0.5) # Extra speed for boost mode
        self.declare_parameter('tilt_step', 0.01) # Step size for tilt control
        self.declare_parameter('z_offset_step', 1.0) # Step size for z position control
        self.declare_parameter('xy_offset_multiplier', 40) # Multiplier for xy position control (max xy originally [-1,1])
        self.declare_parameter('pivot_step', 1.0) # Step size for pivot point adjustment in mm

        # Retrieve parameter values
        self.MAX_SPEED = self.get_parameter('max_speed').value
        self.MAX_ROLL = self.get_parameter('max_roll').value
        self.MAX_PITCH = self.get_parameter('max_pitch').value
        self.MAX_YAW = self.get_parameter('max_yaw').value
        self.MAX_Z_OFFSET = self.get_parameter('max_z_offset').value
        self.BOOST = self.get_parameter('boost').value
        self.TILT_STEP = self.get_parameter('tilt_step').value
        self.Z_OFFSET_STEP = self.get_parameter('z_offset_step').value
        self.XY_OFFSET_MULTIPLIER = self.get_parameter('xy_offset_multiplier').value
        self.PIVOT_STEP = self.get_parameter('pivot_step').value

        # Internally store the posture
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.z_offset = 0.0 # (note: not storing xy offset for now)

        # Internally store the pivot point (no pivot_z control for now)
        self.pivot_x = 0.0
        self.pivot_y = 0.0

        # Store the command type
        self.cmd_type = OrionMotionCmd.CMD_RESET

        # Eyes state
        self.eyes_power = True
        self.eyes_mood = OrionEyesCmd.MOOD_DEFAULT
        self.eyes_gaze_x = 0.0
        self.eyes_gaze_y = 0.0
        self.auto_blink = True
        self.auto_idle = True
        self.prev_mood = OrionEyesCmd.MOOD_DEFAULT
        
        self.persist_gaze_x = 0.0
        self.persist_gaze_y = 0.0

    def operation_reset(self):
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.z_offset = 0.0

    def operation_normal(self, msg) -> Tuple[float, float, float]:
        # --- Boost Mode ---
        # Get the speed multiplier value from R2
        # r2_val = (-msg.axes[BTN_R2] + 1.0) / 2.0 # Normalize from [-1,1] to [0,1] # For PS5 controller only
        r2_val = msg.buttons[BTN_R2] # For Fandragon controller
        speed_multiplier = self.MAX_SPEED + (r2_val * self.BOOST)

        # --- Walking Commands ---
        lin_x = msg.axes[LS_VERT] * speed_multiplier
        lin_y = msg.axes[LS_HORZ] * speed_multiplier
        ang_z = msg.axes[RS_HORZ] * speed_multiplier

        # --- Posture Commands ---
        if msg.axes[DPAD_HORZ] > 0.5: self.roll += self.TILT_STEP
        elif msg.axes[DPAD_HORZ] < -0.5: self.roll -= self.TILT_STEP
        if msg.axes[DPAD_VERT] > 0.5: self.pitch -= self.TILT_STEP
        elif msg.axes[DPAD_VERT] < -0.5: self.pitch += self.TILT_STEP
        if msg.buttons[BTN_SQUARE] == 1: self.yaw += self.TILT_STEP
        if msg.buttons[BTN_CIRCLE] == 1: self.yaw -= self.TILT_STEP
        if msg.buttons[BTN_TRIANGLE] == 1: self.z_offset += self.Z_OFFSET_STEP
        if msg.buttons[BTN_CROSS] == 1: self.z_offset -= self.Z_OFFSET_STEP

        # --- Clamp values to max limits ---
        self.roll = max(-self.MAX_ROLL, min(self.MAX_ROLL, self.roll))
        self.pitch = max(-self.MAX_PITCH, min(self.MAX_PITCH, self.pitch))
        self.yaw = max(-self.MAX_YAW, min(self.MAX_YAW, self.yaw))
        self.z_offset = max(-self.MAX_Z_OFFSET, min(self.MAX_Z_OFFSET, self.z_offset))

        return (lin_x, lin_y, ang_z)

    def operation_extras(self, msg) -> Tuple[float, float]:
        # --- XY Position/Offset Control ---
        # It is important to note that unlike z_offset, x and y offset are not persistant
        # (will reset if joystick goes back to center)
        x_offset = msg.axes[LS_VERT]*self.XY_OFFSET_MULTIPLIER
        y_offset = msg.axes[LS_HORZ]*self.XY_OFFSET_MULTIPLIER

        # --- Pivot Point Control ---
        # TODO: Most likely change this to be just the 9 main points on the dog
        if msg.axes[DPAD_HORZ] > 0.5:  self.pivot_y += self.PIVOT_STEP
        elif msg.axes[DPAD_HORZ] < -0.5: self.pivot_y -= self.PIVOT_STEP
        if msg.axes[DPAD_VERT] > 0.5:  self.pivot_x += self.PIVOT_STEP
        elif msg.axes[DPAD_VERT] < -0.5: self.pivot_x -= self.PIVOT_STEP
        if msg.buttons[BTN_SQUARE] == 1: # Reset pivot point with R1
            self.pivot_x = 0.0
            self.pivot_y = 0.0
        
        return (x_offset, y_offset)

    def operation_eyes(self, msg):
        # Right stick always updates the persistent gaze accumulator
        self.persist_gaze_x += msg.axes[RS_HORZ] * 0.02
        self.persist_gaze_y -= msg.axes[RS_VERT] * 0.02
        self.persist_gaze_x = max(-1.0, min(1.0, self.persist_gaze_x))
        self.persist_gaze_y = max(-1.0, min(1.0, self.persist_gaze_y))

        # 2. Left stick controls absolute gaze, or falls back to persistent gaze if centered
        if (abs(msg.axes[LS_HORZ]) < 0.05) and (abs(msg.axes[LS_VERT]) < 0.05):
            self.eyes_gaze_x = self.persist_gaze_x
            self.eyes_gaze_y = self.persist_gaze_y
        else:
            self.eyes_gaze_x = msg.axes[LS_HORZ]
            self.eyes_gaze_y = -msg.axes[LS_VERT]
            self.eyes_gaze_x = max(-1.0, min(1.0, self.eyes_gaze_x))
            self.eyes_gaze_y = max(-1.0, min(1.0, self.eyes_gaze_y))

        # # Gaze control - persistent
        # if (abs(msg.axes[LS_HORZ]) < 0.05) and (abs(msg.axes[LS_VERT]) < 0.05):
        #     self.eyes_gaze_x += msg.axes[RS_HORZ] * 0.02
        #     self.eyes_gaze_y -= msg.axes[RS_VERT] * 0.02
        #     self.eyes_gaze_x = max(-1.0, min(1.0, self.eyes_gaze_x))
        #     self.eyes_gaze_y = max(-1.0, min(1.0, self.eyes_gaze_y))
        # else:
        #     self.eyes_gaze_x = msg.axes[LS_HORZ]
        #     self.eyes_gaze_y = -msg.axes[LS_VERT]
        #     self.eyes_gaze_x = max(-1.0, min(1.0, self.eyes_gaze_x))
        #     self.eyes_gaze_y = max(-1.0, min(1.0, self.eyes_gaze_y))
        
        if msg.axes[DPAD_VERT] > 0.5:
            self.eyes_mood = OrionEyesCmd.MOOD_DEFAULT
        elif msg.axes[DPAD_VERT] < -0.5:
            self.eyes_mood = OrionEyesCmd.MOOD_HAPPY
        elif msg.axes[DPAD_HORZ] > 0.5:
            self.eyes_mood = OrionEyesCmd.MOOD_CURIOUS
        elif msg.axes[DPAD_HORZ] < -0.5:
            self.eyes_mood = OrionEyesCmd.MOOD_SLEEPING

        if msg.buttons[BTN_L1] == 1:
            # Idle on/off
            if msg.buttons[BTN_SQUARE] == 1:
                self.auto_idle = True
            elif msg.buttons[BTN_CIRCLE] == 1:
                self.auto_idle = False

            # Blink on/off
            if msg.buttons[BTN_TRIANGLE] == 1:
                self.auto_blink = True
            elif msg.buttons[BTN_CROSS] == 1:
                self.auto_blink = False

        else:
            # Power on/off eyes
            if msg.buttons[BTN_SQUARE] == 1:
                self.eyes_power = True
            elif msg.buttons[BTN_CIRCLE] == 1:
                self.eyes_power = False

            # Reset and recenter gaze
            if msg.buttons[BTN_TRIANGLE] == 1:
                self.eyes_gaze_x = 0.0
                self.eyes_gaze_y = 0.0
                self.persist_gaze_x = 0.0
                self.persist_gaze_y = 0.0

    def joy_callback(self, msg):
        lin_x = 0.0
        lin_y = 0.0
        ang_z = 0.0
        x_offset = 0.0
        y_offset = 0.0

        # --- Commands ---
        # No deadman switch required
        if msg.buttons[BTN_R1] == 1:
            self.cmd_type = OrionMotionCmd.CMD_RESET
        elif msg.buttons[BTN_L3] == 1:
            self.cmd_type = OrionMotionCmd.CMD_NORMAL
        elif msg.buttons[BTN_R3] == 1:
            self.cmd_type = OrionMotionCmd.CMD_EXTRAS
        elif msg.buttons[BTN_OPTIONS] == 1:
            self.cmd_type = OrionMotionCmd.CMD_WAVE
        elif msg.buttons[BTN_SHARE] == 1:
            self.cmd_type = OrionMotionCmd.CMD_HEEL
        elif msg.buttons[BTN_L2] == 1:
            self.cmd_type = OrionMotionCmd.CMD_EYES

        # --- Deadman Switch ---
        # Require holding L1 button before accepting any movement or tilt commands
        if msg.buttons[BTN_L1] == 1:
            if self.cmd_type == OrionMotionCmd.CMD_NORMAL: # Normal
                lin_x, lin_y, ang_z = self.operation_normal(msg)
            elif self.cmd_type == OrionMotionCmd.CMD_EXTRAS: # Extras
                x_offset, y_offset = self.operation_extras(msg)
        
        if self.cmd_type == OrionMotionCmd.CMD_RESET:
            self.operation_reset()
        elif self.cmd_type == OrionMotionCmd.CMD_EYES:
            self.operation_eyes(msg)

        # --- Publish Message ---
        # Create and publish motion command message
        motion_msg = OrionMotionCmd()
        motion_msg.cmd_type = self.cmd_type
        motion_msg.lin_x = lin_x
        motion_msg.lin_y = lin_y
        motion_msg.ang_z = ang_z
        motion_msg.roll = self.roll
        motion_msg.pitch = self.pitch
        motion_msg.yaw = self.yaw
        motion_msg.z_offset = self.z_offset
        motion_msg.x_offset = x_offset
        motion_msg.y_offset = y_offset
        motion_msg.pivot_x = self.pivot_x
        motion_msg.pivot_y = self.pivot_y
        self.motion_publisher.publish(motion_msg)

        # Create and publish eyes command message
        eyes_msg = OrionEyesCmd()
        eyes_msg.mood = self.eyes_mood
        eyes_msg.gaze_x = self.eyes_gaze_x
        eyes_msg.gaze_y = self.eyes_gaze_y
        eyes_msg.power = self.eyes_power
        eyes_msg.mood_changed = (self.eyes_mood != self.prev_mood)
        eyes_msg.auto_blink = self.auto_blink
        eyes_msg.auto_idle = self.auto_idle
        eyes_msg.left_eye_scale = 1.0 # cmd_mux_node handles scaling the eyes based on overall motion
        eyes_msg.right_eye_scale = 1.0
        self.eyes_publisher.publish(eyes_msg)
        self.prev_mood = self.eyes_mood

def main(args=None):
    rclpy.init(args=args)
    joystick_node = JoystickParser()
    
    try:
        rclpy.spin(joystick_node)
    except KeyboardInterrupt:
        pass
    finally:
        joystick_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()