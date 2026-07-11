import rclpy
from rclpy.node import Node
from orion_msgs.msg import OrionEyesCmd
import cv2
import numpy as np
import time
import random

class RoboEyes:
    def __init__(self, width, height, bg_color=(0, 0, 0), eye_color=(0, 190, 255)):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.eye_color = eye_color
        self.base_eye_color = eye_color

        # --- Configuration --- at 640x480
        if self.width == 640 and self.height == 480:
            self.eye_w = 120   # Width of one eye
            self.eye_h = 130   # Height
            self.eye_r = 30    # Corner radius
            self.eye_spacing = 40 # Space between eyes

        # --- Configuration --- at 1920 x 1080
        elif self.width == 1920 and self.height == 1080:
            self.eye_w = int(280*1.5)   # Width of one eye
            self.eye_h = int(350*1.5)   # Height
            self.eye_r = int(70*1.5)    # Corner radius
            self.eye_spacing = int(100*1.2) # Space between eyes
        else:
            # Fallback for generic resolutions
            self.eye_w = int(self.width * 0.2)
            self.eye_h = int(self.height * 0.4)
            self.eye_r = int(self.width * 0.05)
            self.eye_spacing = int(self.width * 0.08)
        
        # Moods: 'default', 'happy', 'angry', 'tired', 'confused'
        self.mood = 'default'
        
        # --- Animation State ---
        self.x = 0.0 
        self.y = 0.0
        self.target_x = 0
        self.target_y = 0
        
        # Blink State
        self.auto_blink = True
        self.is_blinking = False
        self.blink_start_time = 0
        self.blink_duration = 0.2
        self.blink_val = 0.0 # 0.0=Open, 1.0=Closed
        self.next_blink_time = time.time() + random.uniform(1, 4)
        
        # Idle State
        self.auto_idle = True
        self.external_gaze = False
        self.next_move_time = time.time() + random.uniform(0.5, 2.0)

    def set_mood(self, mood):
        self.mood = mood

        # Change color based on mood (Note: OpenCV uses BGR format)
        if mood == 'angry':
            self.eye_color = (0, 0, 255) # Pure Red in BGR
        else:
            self.eye_color = self.base_eye_color # Revert to default blue

    def update(self):
        current_time = time.time()
        
        # --- 1. Blink Logic ---
        if self.auto_blink:
            if not self.is_blinking and current_time > self.next_blink_time:
                self.is_blinking = True
                self.blink_start_time = current_time
                self.next_blink_time = current_time + random.uniform(1, 3)
        
        if self.is_blinking:
            t = (current_time - self.blink_start_time) / self.blink_duration
            if t >= 1.0:
                self.is_blinking = False
                self.blink_val = 0.0
            else:
                self.blink_val = np.sin(t * np.pi)
        elif self.auto_blink:
            self.blink_val = 0.0

        # --- 2. Idle Movement ---
        if self.auto_idle and not self.external_gaze:
            if current_time > self.next_move_time:
                if self.width == 640 and self.height == 480:
                    self.target_x = random.randint(-40, 40)
                    self.target_y = random.randint(-30, 30)
                elif self.width == 1920 and self.height == 1080:
                    self.target_x = random.randint(-250, 250)
                    self.target_y = random.randint(-200, 200)
                self.next_move_time = current_time + random.uniform(0.0, 2.0)
        
        # Smooth interpolation
        self.x += (self.target_x - self.x) * 0.1
        self.y += (self.target_y - self.y) * 0.1

        # Override if manually turned off completely
        if not self.auto_idle and not self.auto_blink and not self.external_gaze:
            self.x = 0
            self.y = 0
            self.target_x = 0
            self.target_y = 0

    def draw(self, frame):
        # Clear background
        frame[:] = self.bg_color
        
        cx, cy = self.width // 2, self.height // 2
        
        # Calculate blink height
        cur_h = int(self.eye_h * (1.0 - self.blink_val))
        if cur_h < 0: cur_h = 0
        
        cur_x = int(self.x)
        cur_y = int(self.y)

        # Eye Coordinates
        y_offset_blink = (self.eye_h - cur_h) // 2
        
        lx = cx - self.eye_spacing - self.eye_w + cur_x
        ly = cy - (self.eye_h // 2) + cur_y + y_offset_blink
        
        rx = cx + self.eye_spacing + cur_x
        ry = cy - (self.eye_h // 2) + cur_y + y_offset_blink
        
        # 1. Draw Base Eyes (White / Colored)
        if cur_h > 2:
            self._draw_eye_shape(frame, lx, ly, self.eye_w, cur_h)
            self._draw_eye_shape(frame, rx, ry, self.eye_w, cur_h)
        else:
            cv2.line(frame, (lx, ly+cur_h//2), (lx+self.eye_w, ly+cur_h//2), self.eye_color, 2)
            cv2.line(frame, (rx, ry+cur_h//2), (rx+self.eye_w, ry+cur_h//2), self.eye_color, 2)

        # 2. Draw Mood Overlays (Black Masks)
        if self.mood == 'angry':
            offset = 45
            pts_left = np.array([
                [lx - 10, ly - 50],
                [lx + self.eye_w + 10, ly - 50],
                [lx + self.eye_w + 10, ly + offset],
                [lx, ly]
            ], np.int32)
            cv2.fillPoly(frame, [pts_left], self.bg_color)

            pts_right = np.array([
                [rx - 10, ry - 50],
                [rx + self.eye_w + 10, ry - 50],
                [rx + self.eye_w, ry],
                [rx - 10, ry + offset]
            ], np.int32)
            cv2.fillPoly(frame, [pts_right], self.bg_color)
            
        elif self.mood == 'happy':
            circle_r = self.eye_w 
            offset_up = 20
            center_l = (lx + self.eye_w // 2, ly + cur_h + int(circle_r/2) - offset_up)
            cv2.circle(frame, center_l, circle_r, self.bg_color, -1)
            center_r = (rx + self.eye_w // 2, ry + cur_h + int(circle_r/2) - offset_up)
            cv2.circle(frame, center_r, circle_r, self.bg_color, -1)
            
        elif self.mood == 'tired':
            droop = int(cur_h * 0.4)
            cv2.rectangle(frame, (lx, ly-10), (lx+self.eye_w, ly+droop), self.bg_color, -1)
            cv2.rectangle(frame, (rx, ry-10), (rx+self.eye_w, ry+droop), self.bg_color, -1)

    def _draw_eye_shape(self, img, x, y, w, h):
        color = self.eye_color
        r = self.eye_r
        
        r = min(r, w // 2, h // 2)
        
        if r <= 0:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, -1)
            return

        cv2.circle(img, (x + r, y + r), r, color, -1)
        cv2.circle(img, (x + w - r, y + r), r, color, -1)
        cv2.circle(img, (x + w - r, y + h - r), r, color, -1)
        cv2.circle(img, (x + r, y + h - r), r, color, -1)
        cv2.rectangle(img, (x + r, y), (x + w - r, y + h), color, -1)
        cv2.rectangle(img, (x, y + r), (x + w, y + h - r), color, -1)


class RoboEyesNode(Node):
    def __init__(self):
        super().__init__('roboeyes_node')
        
        # --- Parameter Declarations ---
        self.declare_parameter('width', 1920)
        self.declare_parameter('height', 1080)
        self.declare_parameter('fullscreen', True)
        self.declare_parameter('fps', 60)
        self.declare_parameter('eye_color_r', 255)
        self.declare_parameter('eye_color_g', 190)
        self.declare_parameter('eye_color_b', 0)

        # Retrieve parameters
        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        self.fullscreen = self.get_parameter('fullscreen').value
        self.fps = self.get_parameter('fps').value
        
        # OpenCV uses BGR ordering
        color_b = self.get_parameter('eye_color_b').value
        color_g = self.get_parameter('eye_color_g').value
        color_r = self.get_parameter('eye_color_r').value
        
        # --- Initialize RoboEyes ---
        self.eyes = RoboEyes(self.width, self.height, bg_color=(0,0,0), eye_color=(color_b, color_g, color_r))
        
        # Canvas for drawing
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # OpenCV Window Setup
        self.win_name = "Orion RoboEyes"
        cv2.namedWindow(self.win_name, cv2.WINDOW_NORMAL)
        if self.fullscreen:
            cv2.setWindowProperty(self.win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.resizeWindow(self.win_name, self.width, self.height)

        # --- ROS 2 Subscribers ---
        self.subscription = self.create_subscription(
            OrionEyesCmd,
            'orion_eyes_cmd',
            self.eyes_cmd_callback,
            10
        )

        # --- Timer for Rendering Loop ---
        # Instead of while True loop, integrate OpenCV updates securely into ROS 2 runtime.
        timer_period = 1.0 / float(self.fps) 
        self.timer = self.create_timer(timer_period, self.render_loop)

        self.get_logger().info('RoboEyes Node Started Successfully')

    def eyes_cmd_callback(self, msg):
        # 1. Update Power (Eyes Shut if off)
        if not msg.power:
            self.eyes.blink_val = 1.0 # Force fully closed
            self.eyes.auto_blink = False
        else:
            self.eyes.auto_blink = True
            
        # 2. Update Mood
        if msg.mood == OrionEyesCmd.MOOD_DEFAULT:
            self.eyes.set_mood('default')
        elif msg.mood == OrionEyesCmd.MOOD_HAPPY:
            self.eyes.set_mood('happy')
        elif msg.mood == OrionEyesCmd.MOOD_ANGRY:
            self.eyes.set_mood('angry')
        elif msg.mood == OrionEyesCmd.MOOD_TIRED:
            self.eyes.set_mood('tired')
        else:
            # Fallback for unenumerated animations
            self.eyes.set_mood('default')

        # 3. Update Gaze
        if msg.gaze_locked or abs(msg.gaze_x) > 0.05 or abs(msg.gaze_y) > 0.05:
            self.eyes.external_gaze = True
            
            # Map [-1.0, 1.0] dynamically to pixel limits based on screen size
            if self.width == 1920:
                self.eyes.target_x = int(msg.gaze_x * 250)
                self.eyes.target_y = int(msg.gaze_y * 200)
            elif self.width == 640:
                self.eyes.target_x = int(msg.gaze_x * 40)
                self.eyes.target_y = int(msg.gaze_y * 30)
            else:
                self.eyes.target_x = int(msg.gaze_x * (self.width * 0.1))
                self.eyes.target_y = int(msg.gaze_y * (self.height * 0.1))
        else:
            # Let the eyes randomly wander if no active gaze command is running
            self.eyes.external_gaze = False

    def render_loop(self):
        # Compute animation frames
        self.eyes.update()
        self.eyes.draw(self.canvas)
        
        # Render image via OpenCV
        cv2.imshow(self.win_name, self.canvas)
        cv2.waitKey(1) # Yield execution briefly so OpenCV registers drawing frame

def main(args=None):
    rclpy.init(args=args)
    roboeyes_node = RoboEyesNode()
    
    try:
        rclpy.spin(roboeyes_node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        roboeyes_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()