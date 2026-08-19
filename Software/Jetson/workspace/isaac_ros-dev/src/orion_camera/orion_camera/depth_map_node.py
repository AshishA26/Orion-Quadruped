# Depth node. Note: Build plan file if not present already by using:
#   /usr/src/tensorrt/bin/trtexec --onnx=./models/midas_v21_small_256.onnx --saveEngine=./models/midas_v21_small_256.plan --fp16

import os

import cv2
import numpy as np
import rclpy
from rclpy.node import Node

import pycuda.driver as cuda
import pycuda.autoinit  # noqa: F401  (initializes a CUDA context on import)
import tensorrt as trt

from cv_bridge import CvBridge
from sensor_msgs.msg import Image, CompressedImage

TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

DEFAULT_ENGINE_PATH = os.path.expanduser("./models/midas_v21_small_256.plan")

TRTEXEC_HINT = (
    "No TensorRT engine found at '{path}'. Build it once with:\n"
    "  /usr/src/tensorrt/bin/trtexec --onnx=<midas.onnx> "
    "--saveEngine={path} --fp16"
)

class TRTInference:
    """Minimal wrapper around a single-input/single-output TensorRT engine
    (TensorRT 10.x tensor-address API, as shipped with JetPack 6.x/7.x)."""

    def __init__(self, engine_path: str, logger=None):
        if not os.path.exists(engine_path):
            raise FileNotFoundError(TRTEXEC_HINT.format(path=engine_path))

        if logger:
            logger.info(f"Loading TensorRT engine from {engine_path}")

        with open(engine_path, 'rb') as f, trt.Runtime(TRT_LOGGER) as runtime:
            self.engine = runtime.deserialize_cuda_engine(f.read())
        self.context = self.engine.create_execution_context()
        self.stream = cuda.Stream()

        self.input_name = None
        self.output_name = None
        for i in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(i)
            mode = self.engine.get_tensor_mode(name)
            if mode == trt.TensorIOMode.INPUT:
                self.input_name = name
            else:
                self.output_name = name

        if self.input_name is None or self.output_name is None:
            raise RuntimeError("Engine must have exactly one input and one output tensor.")

        self.input_shape = tuple(self.engine.get_tensor_shape(self.input_name))
        self.output_shape = tuple(self.engine.get_tensor_shape(self.output_name))

        if logger:
            logger.info(f"Engine input '{self.input_name}' shape={self.input_shape}")
            logger.info(f"Engine output '{self.output_name}' shape={self.output_shape}")

        # Pinned host buffers + device buffers, allocated once.
        self.h_input = cuda.pagelocked_empty(trt.volume(self.input_shape), dtype=np.float32)
        self.h_output = cuda.pagelocked_empty(trt.volume(self.output_shape), dtype=np.float32)
        self.d_input = cuda.mem_alloc(self.h_input.nbytes)
        self.d_output = cuda.mem_alloc(self.h_output.nbytes)

        self.context.set_tensor_address(self.input_name, int(self.d_input))
        self.context.set_tensor_address(self.output_name, int(self.d_output))

    def infer(self, input_array: np.ndarray) -> np.ndarray:
        np.copyto(self.h_input, input_array.ravel())
        cuda.memcpy_htod_async(self.d_input, self.h_input, self.stream)
        self.context.execute_async_v3(stream_handle=self.stream.handle)
        cuda.memcpy_dtoh_async(self.h_output, self.d_output, self.stream)
        self.stream.synchronize()
        return self.h_output.reshape(self.output_shape)


class MidasDepthNode(Node):
    def __init__(self):
        super().__init__('midas_depth_node')

        self.declare_parameter('engine_path', DEFAULT_ENGINE_PATH)
        self.declare_parameter('input_size', 256)
        self.declare_parameter('publish_colorized_raw', True)
        self.declare_parameter('jpeg_quality', 100)

        engine_path = str(self.get_parameter('engine_path').value)
        self.input_size = int(self.get_parameter('input_size').value)
        self.publish_colorized_raw = bool(self.get_parameter('publish_colorized_raw').value)
        self.jpeg_quality = int(self.get_parameter('jpeg_quality').value)

        self.trt_infer = TRTInference(engine_path, logger=self.get_logger())

        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

        self.bridge = CvBridge()

        # Subscriptions / publications (remap these at launch as needed)
        self.image_sub = self.create_subscription(Image, "image_raw", self.image_callback, 2)

        # Raw float32 depth map (relative depth, not colorized) - useful for downstream processing
        self.depth_raw_pub = self.create_publisher(Image, "depth_image_raw", 2)

        # Colorized visualizations (raw + compressed)
        self.depth_color_raw_pub = self.create_publisher(Image, "depth_image_color_raw", 2)
        self.depth_color_compressed_pub = self.create_publisher(CompressedImage, "depth_image_color_compressed", 2)

        self.get_logger().info("MiDaS depth node (TensorRT) ready.")

    def image_callback(self, msg: Image):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        img_h, img_w = frame.shape[:2]

        # --- Preprocess ---
        img_input = cv2.resize(frame, (self.input_size, self.input_size))
        img_input = cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB)
        img_input = img_input.astype(np.float32) / 255.0
        img_input = (img_input - self.mean) / self.std
        img_input = np.transpose(img_input, (2, 0, 1))  # HWC -> CHW
        img_input = np.expand_dims(img_input, axis=0)   # add batch dim
        img_input = np.ascontiguousarray(img_input, dtype=np.float32)

        # --- Inference (TensorRT) ---
        depth = self.trt_infer.infer(img_input)
        depth = np.squeeze(depth).astype(np.float32)

        # --- Resize back to original resolution ---
        depth_resized = cv2.resize(depth, (img_w, img_h))

        # --- Publish raw float depth (relative depth values, no colormap) ---
        depth_msg = self.bridge.cv2_to_imgmsg(depth_resized, encoding='32FC1')
        depth_msg.header = msg.header
        self.depth_raw_pub.publish(depth_msg)

        # --- Publish colorized visualization (raw + compressed) ---
        if self.publish_colorized_raw:
            depth_min = float(depth_resized.min())
            depth_max = float(depth_resized.max())
            denom = (depth_max - depth_min) if (depth_max - depth_min) > 1e-6 else 1.0
            depth_norm = (255.0 * (depth_resized - depth_min) / denom).astype(np.uint8)
            depth_color = cv2.applyColorMap(depth_norm, cv2.COLORMAP_JET)

            color_msg = self.bridge.cv2_to_imgmsg(depth_color, encoding='bgr8')
            color_msg.header = msg.header
            self.depth_color_raw_pub.publish(color_msg)

            compressed_msg = CompressedImage()
            compressed_msg.header = msg.header
            compressed_msg.format = 'jpeg'
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            compressed_msg.data = np.array(
                cv2.imencode('.jpg', depth_color, encode_params)[1]
            ).tobytes()
            self.depth_color_compressed_pub.publish(compressed_msg)


def main(args=None):
    rclpy.init(args=args)
    node = MidasDepthNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()