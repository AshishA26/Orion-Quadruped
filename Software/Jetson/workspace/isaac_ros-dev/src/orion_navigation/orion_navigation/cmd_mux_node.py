import rclpy
from rclpy.node import Node
from orion_msgs.msg import OrionMotionCmd
from orion_msgs.msg import OrionEyesCmd

class CmdMux(Node):
    def __init__(self):
        super().__init__('cmd_mux_node')
        
        self.joy_motion_cmd_sub = self.create_subscription(
            OrionMotionCmd,
            'joy_motion_cmd',
            self.joy_motion_cmd_callback,
            10
        )
        self.joy_eyes_cmd_sub = self.create_subscription(
            OrionEyesCmd,
            'joy_eyes_cmd',
            self.joy_eyes_cmd_callback,
            10
        )
        # TODO(orion)
        # self.nav_motion_cmd_sub = self.create_subscription(
        #     OrionMotionCmd,
        #     'nav_motion_cmd',
        #     self.nav_motion_cmd_callback,
        #     10
        # )
        self.orion_motion_cmd_pub = self.create_publisher(OrionMotionCmd, 'orion_motion_cmd', 10)
        self.orion_eyes_cmd_pub = self.create_publisher(OrionEyesCmd, 'orion_eyes_cmd', 10)            

        self.declare_parameter('send_rate_hz', 50.0)
        send_rate = 1.0 / self.get_parameter('send_rate_hz').value

        self.latest_joy_motion = OrionMotionCmd()
        self.latest_joy_eyes = OrionEyesCmd()

        self.pub_timer = self.create_timer(send_rate, self.publish_latest)

    def joy_motion_cmd_callback(self, msg):
        self.latest_joy_motion = msg

    def joy_eyes_cmd_callback(self, msg):
        self.latest_joy_eyes = msg
    
    def publish_latest(self):
        # TODO(orion): For now we directly send joy command to orion_base
        self.orion_motion_cmd_pub.publish(self.latest_joy_motion)
        self.orion_eyes_cmd_pub.publish(self.latest_joy_eyes)

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