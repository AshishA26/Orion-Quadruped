import rclpy
from rclpy.node import Node
from orion_msgs.msg import OrionEyesCmd
import cv2
import numpy as np
import time
import random
import math

class RoboEyes:
    def __init__(self, width, height, eye_w, eye_h, eye_r, eye_spacing,
                 bg_color=(0, 0, 0), eye_color=(255, 150, 0), blink_duration=0.2,
                 blink_interval_min=1.0, blink_interval_max=4.0,
                 idle_interval_min=0.5, idle_interval_max=2.5,
                 gaze_smoothing=0.15, max_gaze_x_bound=0.13, max_gaze_y_bound=0.18,
                 power_transition_speed=0.05, fps=60, power_off_has_line=True):
        self.width = width
        self.height = height      
        self.eye_w = eye_w
        self.eye_h = eye_h
        self.eye_r = eye_r
        self.eye_spacing = eye_spacing
        self.bg_color = bg_color
        self.eye_color = eye_color  
        
        self.mood = 'default'
        
        self.blink_duration = blink_duration
        self.blink_interval_min = blink_interval_min
        self.blink_interval_max = blink_interval_max
        self.idle_interval_min = idle_interval_min
        self.idle_interval_max = idle_interval_max
        self.gaze_smoothing = gaze_smoothing
        self.max_gaze_x_bound = max_gaze_x_bound
        self.max_gaze_y_bound = max_gaze_y_bound
        self.power_transition_speed = power_transition_speed
        self.fps = fps
        self.power_off_has_line = power_off_has_line

        # --- Animation State ---
        self.x = 0.0 
        self.y = 0.0
        self.target_x = 0
        self.target_y = 0
        
        # Blink/Wink State
        self.auto_blink = True
        self.is_blinking = False
        self.is_winking = False
        self.blink_start_time = 0
        self.blink_l = 0.0
        self.blink_r = 0.0
        self.next_blink_time = time.time() + random.uniform(self.blink_interval_min, self.blink_interval_max)
        
        # Shake/Flicker State
        self.hflicker = False # TODO(orion): Unused
        self.vflicker = False # TODO(orion): Unused
        self.off_x = 0
        self.off_y = 0

        # Idle State
        self.auto_idle = True
        self.external_gaze = False
        self.next_move_time = time.time() + random.uniform(self.idle_interval_min, self.idle_interval_max)

        # Eye Scale State (asymmetric curiosity scaling)
        self.left_eye_scale = 1.0
        self.right_eye_scale = 1.0
        self.target_left_scale = 1.0
        self.target_right_scale = 1.0

        self.power = True

    def set_mood(self, mood):
        self.mood = mood

    def trigger_wink(self, right_eye=True): # TODO(orion): Unused
        self.is_winking = True
        self.is_blinking = True
        self.blink_start_time = time.time()
        self.wink_right = right_eye

    def update(self):
        current_time = time.time()
        self.off_x, self.off_y = 0, 0
        
        # --- 1. Blink Logic (Smooth Time-based Sine Wave) ---
        if self.auto_blink and not self.is_blinking and current_time > self.next_blink_time and self.power:
            self.is_blinking = True
            self.is_winking = False
            self.blink_start_time = current_time
            self.next_blink_time = current_time + random.uniform(self.blink_interval_min, self.blink_interval_max)
        
        if self.is_blinking:
            t = (current_time - self.blink_start_time) / self.blink_duration
            if t >= 1.0:
                self.is_blinking = False
                self.is_winking = False
                self.blink_l = 0.0
                self.blink_r = 0.0
            else:
                val = np.sin(t * np.pi)
                if self.is_winking:
                    if self.wink_right:
                        self.blink_r = val
                        self.blink_l = 0.0
                    else:
                        self.blink_l = val
                        self.blink_r = 0.0
                else:
                    self.blink_l = val
                    self.blink_r = val
        else:
            # If power is off, eyes are closed, if power is on, eyes are open
            target = 1.0 if not self.power else 0.0
            transition_speed = 0.05
            self.blink_l += (target - self.blink_l) * transition_speed
            self.blink_r += (target - self.blink_r) * transition_speed

        # --- 2. Idle Movement ---
        if self.auto_idle and not self.external_gaze:
            if current_time > self.next_move_time:
                max_x = int(self.width * self.max_gaze_x_bound)
                max_y = int(self.height * self.max_gaze_y_bound)
                self.target_x = random.randint(-max_x, max_x)
                self.target_y = random.randint(-max_y, max_y)
                self.next_move_time = current_time + random.uniform(self.idle_interval_min, self.idle_interval_max)
        elif not self.auto_idle and not self.external_gaze:
            self.target_x = 0.0
            self.target_y = 0.0
        
        # Smooth interpolation
        self.x += (self.target_x - self.x) * self.gaze_smoothing
        self.y += (self.target_y - self.y) * self.gaze_smoothing

        # --- 3. Shake/Jitter Logic ---
        if self.hflicker:
            self.off_x = random.randint(-15, 15)
        if self.vflicker:
            self.off_y = random.randint(-15, 15)

        # --- 4. Eye Scale Interpolation ---
        self.left_eye_scale += (self.target_left_scale - self.left_eye_scale) * self.gaze_smoothing
        self.right_eye_scale += (self.target_right_scale - self.right_eye_scale) * self.gaze_smoothing

    def draw(self, frame):
        frame[:] = self.bg_color
        cx, cy = self.width // 2, self.height // 2

        def draw_single_eye(ex, ey, ew, eh, er, blink_val, is_left):
            cur_h = int(eh * (1.0 - blink_val))
            if cur_h < 0: cur_h = 0
            
            y_off = (eh - cur_h) // 2
            final_y = ey + y_off + self.off_y
            final_x = ex + self.off_x

            # 1. Base Eye Shape
            if cur_h > 4:
                r = min(er, ew // 2, cur_h // 2)
                if r <= 0:
                    cv2.rectangle(frame, (final_x, final_y), (final_x + ew, final_y + cur_h), self.eye_color, -1)
                else:
                    cv2.rectangle(frame, (final_x + r, final_y), (final_x + ew - r, final_y + cur_h), self.eye_color, -1)
                    cv2.rectangle(frame, (final_x, final_y + r), (final_x + ew, final_y + cur_h - r), self.eye_color, -1)
                    cv2.circle(frame, (final_x + r, final_y + r), r, self.eye_color, -1)
                    cv2.circle(frame, (final_x + ew - r, final_y + r), r, self.eye_color, -1)
                    cv2.circle(frame, (final_x + ew - r, final_y + cur_h - r), r, self.eye_color, -1)
                    cv2.circle(frame, (final_x + r, final_y + cur_h - r), r, self.eye_color, -1)
            else:
                if self.power_off_has_line: # Draw line when power is off and for blinks
                    cv2.line(frame, (final_x, ey + eh // 2 + self.off_y), (final_x + ew, ey + eh // 2 + self.off_y), self.eye_color, 2)
                else: # Draw line only for blinks, not when power is off
                    if self.power:
                        cv2.line(frame, (final_x, ey + eh // 2 + self.off_y), (final_x + ew, ey + eh // 2 + self.off_y), self.eye_color, 2)
                
            if self.mood == 'happy':
                cv2.circle(frame, (final_x + ew // 2, final_y + cur_h + int(ew/2) - 20), ew, self.bg_color, -1)
                
            elif self.mood == 'curious':
                if abs(self.x) > 20:
                    cut = int(eh * 0.25) if (self.x > 0 and is_left) or (self.x < 0 and not is_left) else 0
                    cv2.rectangle(frame, (final_x, final_y - 10), (final_x + ew, final_y + cut), self.bg_color, -1)
                    
            elif self.mood == 'sleeping':
                cv2.rectangle(frame, (final_x, final_y - 10), (final_x + ew, final_y + int(cur_h * 0.4)), self.bg_color, -1)
                cv2.rectangle(frame, (final_x, final_y + int(cur_h * 0.6)), (final_x + ew, final_y + cur_h + 10), self.bg_color, -1)

        # --- Compute scaled eye dimensions (vertical scale only) ---
        l_ew = self.eye_w
        l_eh = int(self.eye_h * self.left_eye_scale)
        l_er = self.eye_r
        r_ew = self.eye_w
        r_eh = int(self.eye_h * self.right_eye_scale)
        r_er = self.eye_r

        # Left eye: original center is at (cx - eye_spacing - eye_w/2, cy)
        l_cx = cx - self.eye_spacing - self.eye_w // 2
        draw_single_eye(l_cx - l_ew // 2 + int(self.x), cy + self.eye_h // 2 + int(self.y) - l_eh, 
                        l_ew, l_eh, l_er, self.blink_l, True)
        # Right eye: original center is at (cx + eye_spacing + eye_w/2, cy)
        r_cx = cx + self.eye_spacing + self.eye_w // 2
        draw_single_eye(r_cx - r_ew // 2 + int(self.x), cy + self.eye_h // 2 + int(self.y) - r_eh, 
                        r_ew, r_eh, r_er, self.blink_r, False)

class RoboEyesNode(Node):
    def __init__(self):
        super().__init__('roboeyes_node')
        
        self.declare_parameter('width', 1920)
        self.declare_parameter('height', 1080)
        self.declare_parameter('eye_w', 420)
        self.declare_parameter('eye_h', 525)
        self.declare_parameter('eye_r', 105)
        self.declare_parameter('eye_spacing', 120)
        self.declare_parameter('fullscreen', True)
        self.declare_parameter('fps', 60)
        self.declare_parameter('eye_color_r', 0)
        self.declare_parameter('eye_color_g', 150)
        self.declare_parameter('eye_color_b', 255)
        self.declare_parameter('blink_duration', 0.2)
        self.declare_parameter('blink_interval_min', 1.0)
        self.declare_parameter('blink_interval_max', 4.0)
        self.declare_parameter('idle_interval_min', 0.5)
        self.declare_parameter('idle_interval_max', 2.5)
        self.declare_parameter('gaze_smoothing', 0.15)
        self.declare_parameter('max_gaze_x_bound', 0.13)
        self.declare_parameter('max_gaze_y_bound', 0.18)
        self.declare_parameter('power_transition_speed', 0.05)
        self.declare_parameter('power_off_has_line', True)

        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        self.fullscreen = self.get_parameter('fullscreen').value
        self.fps = self.get_parameter('fps').value
        color_b = self.get_parameter('eye_color_b').value
        color_g = self.get_parameter('eye_color_g').value
        color_r = self.get_parameter('eye_color_r').value
        
        self.eyes = RoboEyes(
            self.width, self.height,
            eye_w=self.get_parameter('eye_w').value,
            eye_h=self.get_parameter('eye_h').value,
            eye_r=self.get_parameter('eye_r').value,
            eye_spacing=self.get_parameter('eye_spacing').value,
            bg_color=(0, 0, 0),
            eye_color=(color_b, color_g, color_r),
            blink_duration=self.get_parameter('blink_duration').value,
            blink_interval_min=self.get_parameter('blink_interval_min').value,
            blink_interval_max=self.get_parameter('blink_interval_max').value,
            idle_interval_min=self.get_parameter('idle_interval_min').value,
            idle_interval_max=self.get_parameter('idle_interval_max').value,
            gaze_smoothing=self.get_parameter('gaze_smoothing').value,
            max_gaze_x_bound=self.get_parameter('max_gaze_x_bound').value,
            max_gaze_y_bound=self.get_parameter('max_gaze_y_bound').value,
            power_transition_speed=self.get_parameter('power_transition_speed').value,
            fps=self.fps,
            power_off_has_line=self.get_parameter('power_off_has_line').value,
        )
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        self.win_name = "Orion RoboEyes"
        cv2.namedWindow(self.win_name, cv2.WINDOW_NORMAL)
        if self.fullscreen:
            cv2.setWindowProperty(self.win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.resizeWindow(self.win_name, self.width, self.height)

        self.subscription = self.create_subscription(
            OrionEyesCmd,
            'orion_eyes_cmd',
            self.eyes_cmd_callback,
            10
        )

        timer_period = 1.0 / float(self.fps) 
        self.timer = self.create_timer(timer_period, self.render_loop)
        self.get_logger().info('RoboEyes Node Started Successfully')

    def eyes_cmd_callback(self, msg):
        # If transitioning from power off to power on, delay the next blink/move
        if msg.power and not self.eyes.power:
            current_time = time.time()
            # Dynamically calculate transition duration (in seconds)
            transition_duration = 4.6 / (self.eyes.power_transition_speed * self.fps)
            self.eyes.next_blink_time = current_time + transition_duration + random.uniform(self.eyes.blink_interval_min, self.eyes.blink_interval_max)
            self.eyes.next_move_time = current_time + transition_duration + random.uniform(self.eyes.idle_interval_min, self.eyes.idle_interval_max)

        self.eyes.power = msg.power
        if not msg.power:
            self.eyes.auto_blink = False
            self.eyes.auto_idle = False
        else:
            self.eyes.auto_blink = msg.auto_blink
            self.eyes.auto_idle = msg.auto_idle
            
        if msg.mood == OrionEyesCmd.MOOD_HAPPY:
            self.eyes.set_mood('happy')
        elif msg.mood == OrionEyesCmd.MOOD_CURIOUS:
            self.eyes.set_mood('curious')
        elif msg.mood == OrionEyesCmd.MOOD_SLEEPING:
            self.eyes.set_mood('sleeping')
        else:
            self.eyes.set_mood('default')

        if abs(msg.gaze_x) > 0.05 or abs(msg.gaze_y) > 0.05:
            self.eyes.external_gaze = True
            max_x = int(self.width * self.eyes.max_gaze_x_bound)
            max_y = int(self.height * self.eyes.max_gaze_y_bound)
            self.eyes.target_x = int(msg.gaze_x * max_x)
            self.eyes.target_y = int(msg.gaze_y * max_y)
        else:
            self.eyes.external_gaze = False

        self.eyes.target_left_scale = msg.left_eye_scale
        self.eyes.target_right_scale = msg.right_eye_scale

    def render_loop(self):
        self.eyes.update()
        self.eyes.draw(self.canvas)
        cv2.imshow(self.win_name, self.canvas)
        cv2.waitKey(1)

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