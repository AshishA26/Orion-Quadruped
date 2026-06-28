import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

class RoboEyesNode(Node):
    def __init__(self):
        super().__init__('roboeyes_node')
        self.subscription = self.create_subscription(
            Joy,
            'joy',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info(f'I heard: {msg}')

def main(args=None):
    rclpy.init(args=args)
    node = RoboEyesNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()