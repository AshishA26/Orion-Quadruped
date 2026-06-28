import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import serial
import struct
from typing import Tuple

# Command types
CMD_NORMAL = 0x01
CMD_RESET = 0x02
CMD_WAVE = 0x03
CMD_HEEL = 0x04
CMD_DANCE = 0x05
CMD_EXTRAS = 0x06
CMD_EYES = 0x07

# --- Joystick axis and button mapping (PS5 controller) ---
# All settings are in CMD_NORMAL, unless otherwise specified
LS_HORZ = 0 # Strafe left/right if CMD_NORMAL, change y offset if CMD_EXTRAS
LS_VERT = 1 # Move forward/backward if CMD_NORMAL, change x offset if CMD_EXTRAS
RS_HORZ = 2 # Turn left/right
RS_VERT = 5
DPAD_VERT = 7 # Pitch if CMD_NORMAL, move pivot point forward/backward if CMD_EXTRAS
DPAD_HORZ = 6 # Roll if CMD_NORMAL, move pivot point left/right if CMD_EXTRAS
BTN_SQUARE = 0 # Yaw left if CMD_NORMAL, reset pivot point in CMD_EXTRAS
BTN_CROSS = 1 # Height (z offset) decrease
BTN_CIRCLE = 2 # Yaw right
BTN_TRIANGLE = 3 # Height (z offset) increase
BTN_L1 = 4 # Deadman switch
BTN_R1 = 5 # Reset, sets CMD_RESET
BTN_L2 = 3 # Sets CMD_EYES
BTN_R2 = 4 # Boost mode (axis 4)
BTN_SHARE = 8 # Sets CMD_HEEL
BTN_OPTIONS = 9 # Sets CMD_WAVE
BTN_L3 = 10 # Sets CMD_DANCE
BTN_R3 = 11  # Sets CMD_EXTRAS
BTN_PS = 12
BTN_TOUCHPAD = 13 # Sets CMD_NORMAL

class STM32Bridge(Node):
    def __init__(self):
        super().__init__('stm32_bridge_node')
        
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
        self.z_offset = 0.0 # (note: not storing xy offset for now)

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

    def operation_reset(self):
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.z_offset = 0.0

    def operation_normal(self, msg) -> Tuple[float, float, float]:
        # --- Boost Mode ---
        # Get the speed multiplier value from R2
        r2_val = (-msg.axes[BTN_R2] + 1.0) / 2.0 # Normalize from [-1,1] to [0,1]
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

    def joy_callback(self, msg):
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        lin_x = 0.0
        lin_y = 0.0
        ang_z = 0.0
        x_offset = 0.0
        y_offset = 0.0

        # --- Commands ---
        # No deadman switch required
        if msg.buttons[BTN_R1] == 1:
            self.cmd_type = CMD_RESET
            self.operation_reset()
        elif msg.buttons[BTN_TOUCHPAD] == 1:
            self.cmd_type = CMD_NORMAL
        elif msg.buttons[BTN_R3] == 1:
            self.cmd_type = CMD_EXTRAS
        elif msg.buttons[BTN_L3] == 1:
            self.cmd_type = CMD_DANCE
        elif msg.buttons[BTN_OPTIONS] == 1:
            self.cmd_type = CMD_WAVE
        elif msg.buttons[BTN_SHARE] == 1:
            self.cmd_type = CMD_HEEL
        elif msg.axes[BTN_L2] > 0.5: # TODO: Check this value
            self.cmd_type = CMD_EYES
            # This is just set for sending over to stm32.
            # roboeyes_node handles the actual logic.
            
        # --- Deadman Switch ---
        # Require holding L1 button before accepting any movement or tilt commands
        if msg.buttons[BTN_L1] == 1:
            if self.cmd_type == CMD_NORMAL: # Normal
                lin_x, lin_y, ang_z = self.operation_normal(msg)
            elif self.cmd_type == CMD_EXTRAS: # Extras
                x_offset, y_offset = self.operation_extras(msg)

        # --- Pack Data ---
        # '<B9f' = 1 unsigned char (1 byte) + 11 floats (44 bytes) = 45 byte payload
        # Note: If the deadman switch is NOT pressed, this still gets sent continuously
        # with 0 velocity so the STM32 knows we are still connected, preventing timeout disconnects.
        # The `<` indicates Little-Endian byte order (standard for STM32/ARM)
        payload = struct.pack('<B11f', self.cmd_type, lin_x, lin_y, ang_z, 
                                self.roll, self.pitch, self.yaw, 
                                self.z_offset, x_offset, y_offset, 
                                self.pivot_x, self.pivot_y)

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
        # self.get_logger().info(f"Sent: X:{lin_x:.2f}, Y:{lin_y:.2f}, Z:{ang_z:.2f} \
        #     Roll:{math.degrees(self.roll):.1f}, Pitch:{math.degrees(self.pitch):.1f}, Yaw:{math.degrees(self.yaw):.1f}, \
        #     Z Pos:{self.z_offset:.1f}, X Pos:{x_offset:.1f}, Y Pos:{y_offset:.1f}, \
        #     CmdType:{self.cmd_type}, \
        #     PivotX:{self.pivot_x:.1f}, PivotY:{self.pivot_y:.1f}")

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