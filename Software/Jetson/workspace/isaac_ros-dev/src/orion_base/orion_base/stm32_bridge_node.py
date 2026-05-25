import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import struct

class STM32Bridge(Node):
    def __init__(self):
        super().__init__('stm32_bridge_node')
        
        # Configure Serial Port based on your schematic (Jetson Pins 8/10)
        serial_port = '/dev/ttyTHS1'  
        baud_rate = 115200
        
        try:
            self.serial_conn = serial.Serial(serial_port, baud_rate, timeout=0.1)
            self.get_logger().info(f"Successfully opened {serial_port} at {baud_rate} baud.")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to open serial port: {e}")
            self.serial_conn = None

        # Subscribe to standard ROS2 velocity commands
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )

    def calculate_checksum(self, payload_bytes):
        """Simple XOR checksum of the payload"""
        checksum = 0
        for byte in payload_bytes:
            checksum ^= byte
        return checksum

    def cmd_vel_callback(self, msg):
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        # Extract values from the Twist message
        # Linear X: Forward/Back, Linear Y: Strafe Left/Right, Angular Z: Turn
        lin_x = msg.linear.x
        lin_y = msg.linear.y
        ang_z = msg.angular.z

        # Command Type for Velocity is 0x01
        cmd_type = 0x01

        # Pack data using struct: 'B' = unsigned char (1 byte), 'f' = float (4 bytes)
        # The `<` indicates Little-Endian byte order (standard for STM32/ARM)
        payload = struct.pack('<Bfff', cmd_type, lin_x, lin_y, ang_z)
        
        # Calculate checksum on the payload (Type + Floats)
        checksum = self.calculate_checksum(payload)

        # Assemble the full packet
        header = struct.pack('<BB', 0x55, 0xAA)
        footer_checksum = struct.pack('<B', checksum)
        
        full_packet = header + payload + footer_checksum

        # Send over UART
        self.serial_conn.write(full_packet)
        self.get_logger().debug(f"Sent: X:{lin_x:.2f}, Y:{lin_y:.2f}, Z:{ang_z:.2f}")

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