import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
# TODO(orion)
class RoboEyesNode(Node):
    def __init__(self):
        super().__init__('roboeyes_node')
        # self.subscription = self.create_subscription(
        #     Joy,
        #     'joy',
        #     self.listener_callback,
        #     10)
        # self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        # self.get_logger().info(f'I heard: {msg}')
        pass

def main(args=None):
    rclpy.init(args=args)
    roboeyes_node = RoboEyesNode()
    
    try:
        rclpy.spin(roboeyes_node)
    except KeyboardInterrupt:
        pass
    finally:
        roboeyes_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()