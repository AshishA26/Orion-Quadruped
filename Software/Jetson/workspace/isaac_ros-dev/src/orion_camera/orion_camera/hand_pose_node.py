import rclpy
from rclpy.node import Node

from cv_bridge import CvBridge
from sensor_msgs.msg import Image, CompressedImage
from std_msgs.msg import Float32MultiArray

import cv2
import mediapipe as mp
import numpy as np

class HandPoseNode(Node):
    def __init__(self):
        super().__init__('hand_pose_node')
    
        self.declare_parameter('max_num_hands', 1)
        self.declare_parameter('model_complexity', 0)
        self.declare_parameter('min_detection_confidence', 0.6)
        self.declare_parameter('min_tracking_confidence', 0.6)

        max_num_hands = int(self.get_parameter('max_num_hands').value)
        model_complexity = int(self.get_parameter('model_complexity').value)
        min_detection_confidence = float(self.get_parameter('min_detection_confidence').value)
        min_tracking_confidence = float(self.get_parameter('min_tracking_confidence').value)

        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(Image, "image_raw", self.image_callback, 2)
        self.annotated_pub = self.create_publisher(Image, "annotated_image_raw", 2)
        self.landmarks_pub = self.create_publisher(Float32MultiArray, "landmarks", 2)
        self.annotated_compressed_pub = self.create_publisher(CompressedImage, "annotated_image_compressed", 2)

    def image_callback(self, msg: Image):
        # Get the frame, convert to rgb, process it
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        annotated_image = frame.copy()
        landmarks = Float32MultiArray()

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            self.mp_draw.draw_landmarks(
                annotated_image,
                hand_landmarks,
                mp.solutions.hands.HAND_CONNECTIONS,
                self.mp_styles.get_default_hand_landmarks_style(),
                self.mp_styles.get_default_hand_connections_style(),
            )
            landmarks.data = [
                float(v) 
                for lm in hand_landmarks.landmark
                for v in (lm.x, lm.y, lm.z) 
            ]
        else:
            landmarks.data = []

        annotated_msg = self.bridge.cv2_to_imgmsg(annotated_image, encoding='bgr8')
        annotated_msg.header = msg.header

        annotated_compressed_msg = CompressedImage()
        annotated_compressed_msg.header = msg.header
        annotated_compressed_msg.format = 'jpeg'
        annotated_compressed_msg.data = np.array(cv2.imencode('.jpg', annotated_image)[1]).tobytes()

        self.annotated_pub.publish(annotated_msg)
        self.annotated_compressed_pub.publish(annotated_compressed_msg)
        self.landmarks_pub.publish(landmarks)

    def destroy_node(self):
        self.hands.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = HandPoseNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()