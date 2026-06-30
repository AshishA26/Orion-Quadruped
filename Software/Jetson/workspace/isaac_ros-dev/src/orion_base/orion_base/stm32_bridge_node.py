import math
import rclpy
from rclpy.node import Node
from orion_msgs.msg import OrionMotionCmd
import serial
import struct
from typing import Tuple

class STM32Bridge(Node):
    def __init__(self):
        super().__init__('stm32_bridge_node')
        self.motion_subscriber = self.create_subscription(OrionMotionCmd, 'orion_motion_cmd', self.motion_callback, 10)

        # Configure Serial Port (UART)
        self.declare_parameter('serial_port', '/dev/ttyTHS1')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('send_rate_hz', 50.0)
        serial_port = self.get_parameter('serial_port').value
        baud_rate = self.get_parameter('baud_rate').value
        send_rate = 1.0 / self.get_parameter('send_rate_hz').value
        
        try:
            self.serial_conn = serial.Serial(serial_port, baud_rate, timeout=0.1)
            self.get_logger().info(f"Successfully opened {serial_port} at {baud_rate} baud.")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to open serial port: {e}")
            self.serial_conn = None

        self.latest_msg = OrionMotionCmd()
        self.latest_msg.cmd_type = OrionMotionCmd.CMD_NORMAL

        # Create a timer to write to UART
        self.write_timer = self.create_timer(send_rate, self.send_to_stm32)

    def calculate_checksum(self, payload_bytes):
        # Simple XOR checksum of the payload
        checksum = 0
        for byte in payload_bytes:
            checksum ^= byte
        return checksum

    def motion_callback(self, msg):
        # Store the latest command
        self.latest_msg = msg

    def send_to_stm32(self):
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        msg = self.latest_msg

        # --- Pack Data ---
        # '<B11f' = 1 unsigned char (1 byte) + 11 floats (44 bytes) = 45 byte payload
        # Note: If the deadman switch is NOT pressed, this still gets sent continuously
        # with 0 velocity so the STM32 knows we are still connected, preventing timeout disconnects.
        # The `<` indicates Little-Endian byte order (standard for STM32/ARM)
        payload = struct.pack('<B11f', msg.cmd_type, msg.lin_x, msg.lin_y, msg.ang_z, 
                                msg.roll, msg.pitch, msg.yaw, 
                                msg.z_offset, msg.x_offset, msg.y_offset, 
                                msg.pivot_x, msg.pivot_y)

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