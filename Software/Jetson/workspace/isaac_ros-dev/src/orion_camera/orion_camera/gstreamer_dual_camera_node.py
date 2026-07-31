# GStreamer-based dual CSI camera ROS 2 node for IMX219-83.
# Uses the nvarguscamerasrc GStreamer pipeline (proven in dual_camera.py)
# to capture from two CSI sensors and publish as ROS 2 Image/CameraInfo.
#
# This is an alternative to the Isaac ROS Argus solution that works
# without the isaac_ros_argus_camera package.

import threading
import yaml

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo, CompressedImage
from cv_bridge import CvBridge
import numpy as np


class CSICamera:
    """Threaded CSI camera capture via GStreamer, adapted from dual_camera.py."""

    def __init__(self):
        self.video_capture = None
        self.frame = None
        self.grabbed = False
        self.read_thread = None
        self.read_lock = threading.Lock()
        self.running = False

    def open(self, gstreamer_pipeline_string):
        try:
            self.video_capture = cv2.VideoCapture(
                gstreamer_pipeline_string, cv2.CAP_GSTREAMER
            )
            self.grabbed, self.frame = self.video_capture.read()
        except RuntimeError:
            self.video_capture = None
            raise RuntimeError(
                f'Unable to open camera with pipeline: {gstreamer_pipeline_string}'
            )

    def start(self):
        if self.running:
            return self
        if self.video_capture is not None:
            self.running = True
            self.read_thread = threading.Thread(target=self._update, daemon=True)
            self.read_thread.start()
        return self

    def stop(self):
        self.running = False
        if self.read_thread is not None:
            self.read_thread.join(timeout=5.0)
            self.read_thread = None

    def _update(self):
        while self.running:
            try:
                grabbed, frame = self.video_capture.read()
                with self.read_lock:
                    self.grabbed = grabbed
                    self.frame = frame
            except RuntimeError:
                pass

    def read(self):
        with self.read_lock:
            if self.frame is not None:
                return self.grabbed, self.frame.copy()
            return False, None

    def release(self):
        self.stop()
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None


def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    framerate=30,
    flip_method=0,
):
    """Build the nvarguscamerasrc GStreamer pipeline string.

    Same pipeline as dual_camera.py — nvarguscamerasrc captures from the
    CSI sensor, nvvidconv handles color/flip, videoconvert produces BGR
    for OpenCV.
    """
    return (
        'nvarguscamerasrc sensor-id=%d ! '
        'video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, '
        'framerate=(fraction)%d/1 ! '
        'nvvidconv flip-method=%d ! '
        'video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! '
        'videoconvert ! '
        'video/x-raw, format=(string)BGR ! appsink drop=1'
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            capture_width,
            capture_height,
        )
    )


def load_camera_info(yaml_path, node_logger):
    """Load a ROS camera calibration YAML into a CameraInfo message."""
    camera_info = CameraInfo()
    try:
        with open(yaml_path, 'r') as f:
            cal = yaml.safe_load(f)
        camera_info.width = cal['image_width']
        camera_info.height = cal['image_height']
        camera_info.distortion_model = cal.get('distortion_model', 'plumb_bob')
        camera_info.d = [float(x) for x in cal['distortion_coefficients']['data']]
        camera_info.k = [float(x) for x in cal['camera_matrix']['data']]
        camera_info.r = [float(x) for x in cal['rectification_matrix']['data']]
        camera_info.p = [float(x) for x in cal['projection_matrix']['data']]
        node_logger.info(f'Loaded calibration from {yaml_path}')
    except Exception as e:
        node_logger.warn(
            f'Failed to load calibration from {yaml_path}: {e}. '
            'Using empty CameraInfo.'
        )
    return camera_info


class GStreamerDualCameraNode(Node):
    """ROS 2 node publishing dual CSI camera feeds via GStreamer."""

    def __init__(self):
        super().__init__('gstreamer_dual_camera_node')

        # --- Parameters ---
        self.declare_parameter('capture_width', 1920)
        self.declare_parameter('capture_height', 1080)
        self.declare_parameter('framerate', 30)
        self.declare_parameter('flip_method', 0)
        self.declare_parameter('left_camera_info_path', '')
        self.declare_parameter('right_camera_info_path', '')

        self.capture_width = self.get_parameter('capture_width').value
        self.capture_height = self.get_parameter('capture_height').value
        self.framerate = self.get_parameter('framerate').value
        self.flip_method = self.get_parameter('flip_method').value
        left_cal_path = self.get_parameter('left_camera_info_path').value
        right_cal_path = self.get_parameter('right_camera_info_path').value

        # --- Publishers ---
        self.left_image_pub = self.create_publisher(Image, 'left/image_raw', 2)
        self.left_info_pub = self.create_publisher(CameraInfo, 'left/camera_info', 2)
        self.left_image_compressed_pub = self.create_publisher(
            CompressedImage, 'left/image_compressed', 2
        )
        self.right_image_pub = self.create_publisher(Image, 'right/image_raw', 2)
        self.right_info_pub = self.create_publisher(CameraInfo, 'right/camera_info', 2)
        self.right_image_compressed_pub = self.create_publisher(
            CompressedImage, 'right/image_compressed', 2
        )

        self.bridge = CvBridge()

        # --- Load calibration ---
        self.left_camera_info = load_camera_info(left_cal_path, self.get_logger()) \
            if left_cal_path else CameraInfo()
        self.right_camera_info = load_camera_info(right_cal_path, self.get_logger()) \
            if right_cal_path else CameraInfo()

        # --- Open cameras ---
        self.left_camera = CSICamera()
        self.right_camera = CSICamera()

        left_pipeline = gstreamer_pipeline(
            sensor_id=0,
            capture_width=self.capture_width,
            capture_height=self.capture_height,
            framerate=self.framerate,
            flip_method=self.flip_method,
        )
        right_pipeline = gstreamer_pipeline(
            sensor_id=1,
            capture_width=self.capture_width,
            capture_height=self.capture_height,
            framerate=self.framerate,
            flip_method=self.flip_method,
        )

        self.get_logger().info(f'Left pipeline: {left_pipeline}')
        self.get_logger().info(f'Right pipeline: {right_pipeline}')

        self.left_camera.open(left_pipeline)
        self.left_camera.start()
        self.right_camera.open(right_pipeline)
        self.right_camera.start()

        self.get_logger().info('Both CSI cameras opened successfully.')

        # --- Timer for publishing ---
        timer_period = 1.0 / self.framerate
        self.timer = self.create_timer(timer_period, self._publish_frames)

    def _publish_frames(self):
        now = self.get_clock().now().to_msg()

        # Left camera
        grabbed_l, frame_l = self.left_camera.read()
        if grabbed_l and frame_l is not None:
            img_msg = self.bridge.cv2_to_imgmsg(frame_l, encoding='bgr8')
            img_msg.header.stamp = now
            img_msg.header.frame_id = 'left_camera'
            self.left_image_pub.publish(img_msg)

            compressed_msg = CompressedImage()
            compressed_msg.header.stamp = now
            compressed_msg.header.frame_id = 'left_camera'
            compressed_msg.format = 'jpeg'
            compressed_msg.data = np.array(cv2.imencode('.jpg', frame_l)[1]).tobytes()
            self.left_image_compressed_pub.publish(compressed_msg)

            self.left_camera_info.header.stamp = now
            self.left_camera_info.header.frame_id = 'left_camera'
            self.left_info_pub.publish(self.left_camera_info)

        # Right camera
        grabbed_r, frame_r = self.right_camera.read()
        if grabbed_r and frame_r is not None:
            img_msg = self.bridge.cv2_to_imgmsg(frame_r, encoding='bgr8')
            img_msg.header.stamp = now
            img_msg.header.frame_id = 'right_camera'
            self.right_image_pub.publish(img_msg)

            compressed_msg = CompressedImage()
            compressed_msg.header.stamp = now
            compressed_msg.header.frame_id = 'right_camera'
            compressed_msg.format = 'jpeg'
            compressed_msg.data = np.array(cv2.imencode('.jpg', frame_r)[1]).tobytes()
            self.right_image_compressed_pub.publish(compressed_msg)

            self.right_camera_info.header.stamp = now
            self.right_camera_info.header.frame_id = 'right_camera'
            self.right_info_pub.publish(self.right_camera_info)

    def destroy_node(self):
        self.get_logger().info('Shutting down cameras...')
        self.left_camera.release()
        self.right_camera.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GStreamerDualCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
