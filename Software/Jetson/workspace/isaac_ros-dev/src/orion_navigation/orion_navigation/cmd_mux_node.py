import rclpy
from rclpy.node import Node
from orion_msgs.msg import OrionMotionCmd
from orion_msgs.msg import OrionEyesCmd
from typing import Tuple
# TODO(orion)
class CmdMux(Node):
    def __init__(self):
        super().__init__('cmd_mux_node')
        # self.subscription

    def listener_callback(self, msg):
        # self.get_logger().info(f'I heard: {msg}')
        pass

def main(args=None):
    rclpy.init(args=args)
    cmd_mux_node = CmdMux()
    
    try:
        rclpy.spin(cmd_mux_node)
    except KeyboardInterrupt:
        pass
    finally:
        cmd_mux_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()