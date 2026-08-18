import math

import rclpy
from rclpy.node import Node

from orion_msgs.msg import OrionLegInfo
from sensor_msgs.msg import JointState


class JointStateRepublisher(Node):
    def __init__(self):
        super().__init__('joint_state_republisher')

        # Subscribe independently to each leg
        self.front_left_sub = self.create_subscription(
            OrionLegInfo,
            '/joint_angles_front_left',
            self.front_left_callback,
            10
        )

        self.front_right_sub = self.create_subscription(
            OrionLegInfo,
            '/joint_angles_front_right',
            self.front_right_callback,
            10
        )

        self.back_left_sub = self.create_subscription(
            OrionLegInfo,
            '/joint_angles_back_left',
            self.back_left_callback,
            10
        )

        self.back_right_sub = self.create_subscription(
            OrionLegInfo,
            '/joint_angles_back_right',
            self.back_right_callback,
            10
        )

        # All legs publish to the same /joint_states topic
        self.joint_state_pub = self.create_publisher(
            JointState,
            '/joint_states',
            10
        )

        # Same corrections as the STM32 bridge
        self.FEMUR_OFFSET_DEG = 37.756404876708984
        self.TIBIA_OFFSET_DEG = 98.46704864501953

        self.get_logger().info(
            'JointStateRepublisher started'
        )

    def front_left_callback(self, msg):
        joint_state = JointState()

        joint_state.header.stamp = self.get_clock().now().to_msg()

        joint_state.name = [
            'front_left_joint_1',
            'front_left_joint_2',
            'front_left_joint_3',
        ]

        corrected = [
            msg.hip_angle,
            msg.femur_angle + self.FEMUR_OFFSET_DEG,
            msg.tibia_angle - self.TIBIA_OFFSET_DEG,
        ]

        joint_state.position = [
            math.radians(angle)
            for angle in corrected
        ]

        self.joint_state_pub.publish(joint_state)

    def front_right_callback(self, msg):
        joint_state = JointState()

        joint_state.header.stamp = self.get_clock().now().to_msg()

        joint_state.name = [
            'front_right_joint_1',
            'front_right_joint_2',
            'front_right_joint_3',
        ]

        corrected = [
            msg.hip_angle,
            msg.femur_angle - self.FEMUR_OFFSET_DEG,
            msg.tibia_angle + self.TIBIA_OFFSET_DEG,
        ]

        joint_state.position = [
            math.radians(angle)
            for angle in corrected
        ]

        self.joint_state_pub.publish(joint_state)

    def back_left_callback(self, msg):
        joint_state = JointState()

        joint_state.header.stamp = self.get_clock().now().to_msg()

        joint_state.name = [
            'back_left_joint_1',
            'back_left_joint_2',
            'back_left_joint_3',
        ]

        corrected = [
            msg.hip_angle,
            msg.femur_angle + self.FEMUR_OFFSET_DEG,
            msg.tibia_angle - self.TIBIA_OFFSET_DEG,
        ]

        joint_state.position = [
            math.radians(angle)
            for angle in corrected
        ]

        self.joint_state_pub.publish(joint_state)

    def back_right_callback(self, msg):
        joint_state = JointState()

        joint_state.header.stamp = self.get_clock().now().to_msg()

        joint_state.name = [
            'back_right_joint_1',
            'back_right_joint_2',
            'back_right_joint_3',
        ]

        corrected = [
            msg.hip_angle,
            msg.femur_angle - self.FEMUR_OFFSET_DEG,
            msg.tibia_angle + self.TIBIA_OFFSET_DEG,
        ]

        joint_state.position = [
            math.radians(angle)
            for angle in corrected
        ]

        self.joint_state_pub.publish(joint_state)


def main(args=None):
    rclpy.init(args=args)

    node = JointStateRepublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()