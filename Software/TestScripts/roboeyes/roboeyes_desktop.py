import cv2
import numpy as np
import time
import random

# Blink animation is nice
# Best and most robust version
class RoboEyes:
    def __init__(self, width, height, bg_color=(0, 0, 0), eye_color=(255, 190, 0)):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.eye_color = eye_color
        
        # --- Configuration --- at 640x480
        if self.width == 640 and self.height == 480:
            self.eye_w = 120   # Width of one eye
            self.eye_h = 130   # Height
            self.eye_r = 30    # Corner radius
            self.eye_spacing = 40 # Space between eyes

        # --- Configuration --- at 1920 x 1080
        if self.width == 1920 and self.height == 1080:
            self.eye_w = int(280*1.5)   # Width of one eye
            self.eye_h = int(350*1.5)   # Height
            self.eye_r = int(70*1.5)    # Corner radius
            self.eye_spacing = int(100*1.2) # Space between eyes
        
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
        self.next_move_time = time.time() + random.uniform(0.5, 2.0)

    def set_mood(self, mood):
        self.mood = mood

    def update(self):
        current_time = time.time()
        
        # --- 1. Blink Logic ---
        if self.auto_blink:
            if not self.is_blinking and current_time > self.next_blink_time:
                self.is_blinking = True
                self.blink_start_time = current_time
                self.next_blink_time = current_time + random.uniform(2, 6)
        
        if self.is_blinking:
            t = (current_time - self.blink_start_time) / self.blink_duration
            if t >= 1.0:
                self.is_blinking = False
                self.blink_val = 0.0
            else:
                # Sine wave for smooth open-close-open
                self.blink_val = np.sin(t * np.pi)
        else:
            self.blink_val = 0.0

        # --- 2. Idle Movement ---
        if self.auto_idle:
            if current_time > self.next_move_time:
                if self.width == 640 and self.height == 480:
                    self.target_x = random.randint(-40, 40)
                    self.target_y = random.randint(-30, 30)
                if self.width == 1920 and self.height == 1080:
                    self.target_x = random.randint(-250, 250)
                    self.target_y = random.randint(-200, 200)
                self.next_move_time = current_time + random.uniform(1.0, 3.0)
        
        # Smooth interpolation
        self.x += (self.target_x - self.x) * 0.1
        self.y += (self.target_y - self.y) * 0.1

    def draw(self, frame):
        # Clear background
        frame[:] = self.bg_color
        
        cx, cy = self.width // 2, self.height // 2
        
        # Calculate blink height
        # We modify the height directly to simulate eyelids
        cur_h = int(self.eye_h * (1.0 - self.blink_val))
        if cur_h < 0: cur_h = 0
        
        cur_x = int(self.x)
        cur_y = int(self.y)

        # Eye Coordinates (Top-Left based)
        # We center the eye vertically based on the *original* height
        # so it closes towards the center
        y_offset_blink = (self.eye_h - cur_h) // 2
        
        lx = cx - self.eye_spacing - self.eye_w + cur_x
        ly = cy - (self.eye_h // 2) + cur_y + y_offset_blink
        
        rx = cx + self.eye_spacing + cur_x
        ry = cy - (self.eye_h // 2) + cur_y + y_offset_blink
        
        # 1. Draw Base Eyes (White)
        if cur_h > 2:
            self._draw_eye_shape(frame, lx, ly, self.eye_w, cur_h)
            self._draw_eye_shape(frame, rx, ry, self.eye_w, cur_h)
        else:
            # Draw a thin line when fully blinked
            cv2.line(frame, (lx, ly+cur_h//2), (lx+self.eye_w, ly+cur_h//2), self.eye_color, 2)
            cv2.line(frame, (rx, ry+cur_h//2), (rx+self.eye_w, ry+cur_h//2), self.eye_color, 2)

        # 2. Draw Mood Overlays (Black Masks)
        # We draw black polygons *over* the eyes to shape them.
        
        if self.mood == 'angry':
            offset = 45 # How steep the angle is
            
            # --- Left Eye Mask (\ slope) ---
            # We want to keep the Top-Left, but cut the Top-Right.
            # Mask Polygon: (Top-Left-ish), (Top-Right-Low), (Top-Right-Up), (Top-Left-Up)
            
            # Start the cut at the top-left corner (lx, ly)
            # End the cut at the right side, lower down (lx + w, ly + offset)
            pts_left = np.array([
                [lx - 10, ly - 50],             # Top-Left (Outside)
                [lx + self.eye_w + 10, ly - 50], # Top-Right (Outside)
                [lx + self.eye_w + 10, ly + offset], # Cut point (Low Right)
                [lx, ly]                        # Pivot point (Top Left)
            ], np.int32)
            cv2.fillPoly(frame, [pts_left], self.bg_color)

            # --- Right Eye Mask (/ slope) ---
            # We want to keep the Top-Right, but cut the Top-Left.
            
            # Start the cut at the left side, lower down (rx, ry + offset)
            # End the cut at the top-right corner (rx + w, ry)
            pts_right = np.array([
                [rx - 10, ry - 50],             # Top-Left (Outside)
                [rx + self.eye_w + 10, ry - 50], # Top-Right (Outside)
                [rx + self.eye_w, ry],          # Pivot point (Top Right)
                [rx - 10, ry + offset]          # Cut point (Low Left)
            ], np.int32)
            cv2.fillPoly(frame, [pts_right], self.bg_color)
            
        elif self.mood == 'happy':
            # Happy eyes usually look like inverted crescents (cheek pushing up)
            # We cut the BOTTOM of the eye with a circle
            circle_r = self.eye_w 
            offset_up = 20 # Push the cheek up
            
            # Left Eye Mask
            center_l = (lx + self.eye_w // 2, ly + cur_h + int(circle_r/2) - offset_up)
            cv2.circle(frame, center_l, circle_r, self.bg_color, -1)
            
            # Right Eye Mask
            center_r = (rx + self.eye_w // 2, ry + cur_h + int(circle_r/2) - offset_up)
            cv2.circle(frame, center_r, circle_r, self.bg_color, -1)
            
        elif self.mood == 'tired':
            # Eyelids drooping (cut top half straight)
            droop = int(cur_h * 0.4)
            cv2.rectangle(frame, (lx, ly-10), (lx+self.eye_w, ly+droop), self.bg_color, -1)
            cv2.rectangle(frame, (rx, ry-10), (rx+self.eye_w, ry+droop), self.bg_color, -1)

    def _draw_eye_shape(self, img, x, y, w, h):
        color = self.eye_color
        r = self.eye_r
        
        # Dynamic radius (prevent drawing errors if eye gets too small during blink)
        r = min(r, w // 2, h // 2)
        
        if r <= 0:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, -1)
            return

        # Top-Left
        cv2.circle(img, (x + r, y + r), r, color, -1)
        # Top-Right
        cv2.circle(img, (x + w - r, y + r), r, color, -1)
        # Bottom-Right
        cv2.circle(img, (x + w - r, y + h - r), r, color, -1)
        # Bottom-Left
        cv2.circle(img, (x + r, y + h - r), r, color, -1)
        
        # Inner Rects
        cv2.rectangle(img, (x + r, y), (x + w - r, y + h), color, -1)
        cv2.rectangle(img, (x, y + r), (x + w, y + h - r), color, -1)

# --- Main Application Loop ---
def main():
    WIN_NAME = "RoboEyes Port"
    # WIDTH, HEIGHT = 640, 480
    WIDTH, HEIGHT = 1920, 1080
    
    cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
    if WIDTH==640 and HEIGHT==480:
        cv2.resizeWindow(WIN_NAME, WIDTH, HEIGHT)
    elif WIDTH==1920 and HEIGHT==1080:
        cv2.setWindowProperty(WIN_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    eyes = RoboEyes(WIDTH, HEIGHT)
    
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    print("Keys: [q]uit, [h]appy, [a]ngry, [t]ired, [d]efault")
    
    while True:
        eyes.update()
        eyes.draw(canvas)
        
        cv2.imshow(WIN_NAME, canvas)
        
        key = cv2.waitKey(16) & 0xFF
        if key == ord('q'): break
        elif key == ord('h'): eyes.set_mood('happy')
        elif key == ord('a'): eyes.set_mood('angry')
        elif key == ord('t'): eyes.set_mood('tired')
        elif key == ord('d'): eyes.set_mood('default')

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
