import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import serial
import struct

# Command types
CMD_NORMAL = 0x01
CMD_RESET = 0x02
CMD_WAVE = 0x03
CMD_HEEL = 0x04

# Joystick axis and button mapping (PS5 controller)
LS_HORZ = 0 # Strafe left/right
LS_VERT = 1 # Forward/backward
RS_HORZ = 2 # Turn left/right
RS_VERT = 5
DPAD_VERT = 7 # Pitch (or move pivot point forward/backward when R3 held)
DPAD_HORZ = 6 # Roll (or move pivot point left/right when R3 held)
BTN_SQUARE = 0 # Yaw left
BTN_CROSS = 1 # Height decrease
BTN_CIRCLE = 2 # Yaw right
BTN_TRIANGLE = 3 # Height increase
BTN_L1 = 4 # Deadman switch
BTN_R1 = 5 # Reset (when holding L1 or R3)
BTN_L2 = 3
BTN_R2 = 4 # Boost mode (axis 4, or button 7 when fully pressed)
BTN_SHARE = 8 # Heel
BTN_OPTIONS = 9 # Wave
BTN_L3 = 10
BTN_R3 = 11  # Hold to control pivot point
BTN_PS = 12
BTN_TOUCHPAD = 13 # Set command to CMD_NORMAL

class STM32Bridge(Node):
    def __init__(self):
        super().__init__('stm32_bridge_node')
        
        # Parameters
        self.declare_parameter('max_speed', 1.0) # Max speed in m/s or rad/s
        self.declare_parameter('max_roll', math.radians(20)) # +/- 20 degrees
        self.declare_parameter('max_pitch', math.radians(25)) # +/- 25 degrees
        self.declare_parameter('max_yaw', math.radians(30)) # +/- 30 degrees
        self.declare_parameter('max_z', 200.0) # Maximum height in mm
        self.declare_parameter('min_z', 80.0) # Minimum height in mm
        self.declare_parameter('boost', 0.5) # Extra speed for boost mode
        self.declare_parameter('tilt_step', 0.01) # Step size for tilt control
        self.declare_parameter('height_step', 1.0) # Step size for height control
        self.declare_parameter('pivot_step', 1.0) # Step size for pivot point adjustment in mm

        # Retrieve parameter values
        self.MAX_SPEED = self.get_parameter('max_speed').value
        self.MAX_ROLL = self.get_parameter('max_roll').value
        self.MAX_PITCH = self.get_parameter('max_pitch').value
        self.MAX_YAW = self.get_parameter('max_yaw').value
        self.MAX_Z = self.get_parameter('max_z').value
        self.MIN_Z = self.get_parameter('min_z').value
        self.BOOST = self.get_parameter('boost').value
        self.TILT_STEP = self.get_parameter('tilt_step').value
        self.HEIGHT_STEP = self.get_parameter('height_step').value
        self.PIVOT_STEP = self.get_parameter('pivot_step').value

        # Configure Serial Port (UART)
        serial_port = '/dev/ttyTHS1'  
        baud_rate = 115200
        
        try:
            self.serial_conn = serial.Serial(serial_port, baud_rate, timeout=0.1)
            self.get_logger().info(f"Successfully opened {serial_port} at {baud_rate} baud.")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to open serial port: {e}")
            self.serial_conn = None

        # Subscribe to raw joystick commands
        self.subscription = self.create_subscription(
            Joy, # Message type
            'joy', # Topic
            self.joy_callback, # Callback function
            10
        )

        # Internally store the posture
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.z_height = 160.0 # Default height

        # Internally store the pivot point (no pivot_z control for now)
        self.pivot_x = 0.0
        self.pivot_y = 0.0

        # Store the command type
        self.cmd_type = CMD_NORMAL

    def calculate_checksum(self, payload_bytes):
        # Simple XOR checksum of the payload
        checksum = 0
        for byte in payload_bytes:
            checksum ^= byte
        return checksum

    def joy_callback(self, msg):
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        lin_x = 0.0
        lin_y = 0.0
        ang_z = 0.0

        # --- Deadman Switch ---
        # Require holding L1 button before accepting any commands
        if msg.buttons[BTN_L1] == 1:

            # --- Special commands ---
            if msg.buttons[BTN_R1] == 1: # Reset
                self.cmd_type = CMD_RESET
                self.roll = 0.0
                self.pitch = 0.0
                self.yaw = 0.0
                self.z_height = 160.0
            elif msg.buttons[BTN_OPTIONS] == 1: # Wave
                self.cmd_type = CMD_WAVE
            elif msg.buttons[BTN_SHARE] == 1: # Heel
                self.cmd_type = CMD_HEEL
            elif msg.buttons[BTN_TOUCHPAD] == 1: # Normal mode 
                self.cmd_type = CMD_NORMAL

            # Only allow movement actions if in normal mode
            if self.cmd_type == CMD_NORMAL:
                # -- Boost Mode ---
                # Get the speed multiplier value from R2
                r2_val = (-msg.axes[BTN_R2] + 1.0) / 2.0 # Normalize from [-1,1] to [0,1]
                speed_multiplier = self.MAX_SPEED + (r2_val * self.BOOST)

                # --- Walking Commands ---
                lin_x = msg.axes[LS_VERT] * speed_multiplier
                lin_y = msg.axes[LS_HORZ] * speed_multiplier
                ang_z = msg.axes[RS_HORZ] * speed_multiplier

                # --- Posture Commands ---
                if msg.axes[DPAD_HORZ] > 0.5: self.roll += self.TILT_STEP       # Dpad Left
                if msg.axes[DPAD_HORZ] < -0.5: self.roll -= self.TILT_STEP      # Dpad Right
                if msg.axes[DPAD_VERT] > 0.5: self.pitch += self.TILT_STEP      # Dpad Up
                if msg.axes[DPAD_VERT] < -0.5: self.pitch -= self.TILT_STEP     # Dpad Down

                if msg.buttons[BTN_SQUARE] == 1: self.yaw += self.TILT_STEP  # Square
                if msg.buttons[BTN_CIRCLE] == 1: self.yaw -= self.TILT_STEP  # Circle

                if msg.buttons[BTN_TRIANGLE] == 1: self.z_height += self.HEIGHT_STEP # Triangle
                if msg.buttons[BTN_CROSS] == 1: self.z_height -= self.HEIGHT_STEP # Cross

        # --- Pivot Point Control ---
        # If R3 is held, use the Dpad to adjust the pivot point
        if msg.buttons[BTN_R3] == 1:
            if msg.axes[DPAD_HORZ] > 0.5:  self.pivot_y += self.PIVOT_STEP   # Dpad Left
            if msg.axes[DPAD_HORZ] < -0.5: self.pivot_y -= self.PIVOT_STEP   # Dpad Right
            if msg.axes[DPAD_VERT] > 0.5:  self.pivot_x += self.PIVOT_STEP   # Dpad Up
            if msg.axes[DPAD_VERT] < -0.5: self.pivot_x -= self.PIVOT_STEP   # Dpad Down
            if msg.buttons[BTN_R1] == 1: # Reset pivot point with R1
                self.pivot_x = 0.0
                self.pivot_y = 0.0

        # --- Clamp values to max limits ---
        self.roll = max(-self.MAX_ROLL, min(self.MAX_ROLL, self.roll))
        self.pitch = max(-self.MAX_PITCH, min(self.MAX_PITCH, self.pitch))
        self.yaw = max(-self.MAX_YAW, min(self.MAX_YAW, self.yaw))
        self.z_height = max(self.MIN_Z, min(self.MAX_Z, self.z_height))

        # --- Pack Data ---
        # '<B9f' = 1 unsigned char (1 byte) + 9 floats (36 bytes) = 37 byte payload
        # Note: If the deadman switch is NOT pressed, this still gets sent continuously
        # with 0 velocity so the STM32 knows we are still connected, preventing timeout disconnects.
        # The `<` indicates Little-Endian byte order (standard for STM32/ARM)
        payload = struct.pack('<B9f', self.cmd_type, lin_x, lin_y, ang_z, 
                                self.roll, self.pitch, self.yaw, 
                                self.z_height, self.pivot_x, self.pivot_y)

        # Calculate checksum (parity) on the payload (Type + Floats)
        checksum = self.calculate_checksum(payload)

        # Make header and footer of packet
        # The header act as a synchronization marker to mark start of the packet.
        # - 0x55 in binary is 01010101 and 0xAA in binary is 10101010
        # - They create a perfectly alternating pattern of highs and lows on the physical wire
        #   making it easy for reciever to synchronize its timing to the incoming signal. 
        # - It also makes it very easy to spot the start of a packet if on an oscilloscope.
        # - Using two specific bytes instead of a single byte makes it highly unlikely that 
        #   the data bytes will accidentally form that exact sequence and trigger a false start.
        # The footer contains the checksum, which the receiver will also calculate based on the
        # recieved data, to ensure no data corruption.
        header = struct.pack('<BB', 0x55, 0xAA)
        footer_checksum = struct.pack('<B', checksum)

        # Assemble packet
        full_packet = header + payload + footer_checksum

        # Send over UART
        self.serial_conn.write(full_packet)
        self.get_logger().info(f"Sent: X:{lin_x:.2f}, Y:{lin_y:.2f}, Z:{ang_z:.2f} \
            Roll:{math.degrees(self.roll):.1f}, Pitch:{math.degrees(self.pitch):.1f}, \
            Yaw:{math.degrees(self.yaw):.1f}, Height:{self.z_height:.1f}, CmdType:{self.cmd_type}, \
            PivotX:{self.pivot_x:.1f}, PivotY:{self.pivot_y:.1f}")

def main(args=None):
    rclpy.init(args=args)
    bridge_node = STM32Bridge()
    
    try:
        rclpy.spin(bridge_node)
    except KeyboardInterrupt:
        pass
    finally:
        if bridge_node.serial_conn and bridge_node.serial_conn.is_open:
            bridge_node.serial_conn.close()
        bridge_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()