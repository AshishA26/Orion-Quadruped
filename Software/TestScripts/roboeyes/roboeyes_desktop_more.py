import cv2
import numpy as np
import time
import random

# blink animation seems slower
# Some states (curious) are glitchy
class RoboEyes:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.bg_color = (0, 0, 0)
        self.eye_color = (255, 190, 0)
        
        # --- Global Config (Tunable) ---
        self.eye_w = 120
        self.eye_h = 130
        self.eye_r = 30
        self.eye_spacing = 40
        self.cyclops = False
        self.curiosity_effect = True # Scary/Curious logic
        
        # Per-eye overrides (for winking or asymmetry)
        self.l_eye_w, self.l_eye_h, self.l_eye_r = self.eye_w, self.eye_h, self.eye_r
        self.r_eye_w, self.r_eye_h, self.r_eye_r = self.eye_w, self.eye_h, self.eye_r

        # --- States ---
        self.mood = 'default'
        self.x, self.y = 0.0, 0.0
        self.target_x, self.target_y = 0, 0
        
        # Animation values (0.0 to 1.0)
        self.blink_l, self.blink_r = 0.0, 0.0
        self.is_winking = False
        self.shake_x, self.shake_y = 0, 0 # For confuse/laugh
        
        # Timers
        self.auto_blink = True
        self.auto_idle = True
        self.next_blink = time.time() + 2
        self.next_move = time.time() + 1

    def set_mood(self, mood): self.mood = mood.lower()

    def update(self):
        now = time.time()
        # 1. Auto Blink
        if self.auto_blink and now > self.next_blink and not self.is_winking:
            self.blink_l = self.blink_r = 1.0
            self.next_blink = now + random.uniform(2, 6)
        
        # Decay blinks back to 0 (smooth opening)
        self.blink_l = max(0, self.blink_l - 0.15)
        self.blink_r = max(0, self.blink_r - 0.15)
        if self.blink_l == 0: self.is_winking = False

        # 2. Auto Idle
        if self.auto_idle and now > self.next_move:
            self.target_x = random.randint(-50, 50)
            self.target_y = random.randint(-30, 30)
            self.next_move = now + random.uniform(1, 4)
        
        self.x += (self.target_x - self.x) * 0.1
        self.y += (self.target_y - self.y) * 0.1

    def wink(self, right=True):
        self.is_winking = True
        if right: self.blink_r = 1.0
        else: self.blink_l = 1.0

    def draw(self, frame):
        frame[:] = self.bg_color
        cx, cy = self.width // 2, self.height // 2
        
        # Helper to draw single eye
        def draw_eye(ex, ey, ew, eh, er, blink_val, is_left):
            
            if self.mood == 'angry':
                self.eye_color = (0, 0, 255)
            else:
                self.eye_color = (255, 190, 0)
            # Apply blink
            cur_h = int(eh * (1.0 - blink_val))
            y_off = (eh - cur_h) // 2
            
            # Base Rounded Rect
            if cur_h > 4:
                rect_y = ey + y_off
                r = min(er, ew//2, cur_h//2)
                # Drawing manually to ensure no OpenCV errors with small radius
                cv2.rectangle(frame, (ex+r, rect_y), (ex+ew-r, rect_y+cur_h), self.eye_color, -1)
                cv2.rectangle(frame, (ex, rect_y+r), (ex+ew, rect_y+cur_h-r), self.eye_color, -1)
                for pt in [(ex+r, rect_y+r), (ex+ew-r, rect_y+r), (ex+ew-r, rect_y+cur_h-r), (ex+r, rect_y+cur_h-r)]:
                    cv2.circle(frame, pt, r, self.eye_color, -1)
            else:
                cv2.line(frame, (ex, ey+eh//2), (ex+ew, ey+eh//2), self.eye_color, 2)

            # --- Mood Masks ---
            mask_y = ey + y_off
            if self.mood == 'angry':
                pts = [[ex, mask_y], [ex+ew, mask_y+40], [ex+ew, mask_y-50], [ex, mask_y-50]] if is_left else \
                      [[ex, mask_y+40], [ex+ew, mask_y], [ex+ew, mask_y-50], [ex, mask_y-50]]
                cv2.fillPoly(frame, [np.array(pts, np.int32)], self.bg_color)
            
            elif self.mood == 'happy':
                cv2.circle(frame, (ex+ew//2, mask_y+cur_h+40), ew, self.bg_color, -1)
            
            elif self.mood == 'scary':
                # Scary has "pinched" eyes, cutting top and bottom
                cv2.rectangle(frame, (ex, mask_y-10), (ex+ew, mask_y+25), self.bg_color, -1)
                cv2.rectangle(frame, (ex, mask_y+cur_h-25), (ex+ew, mask_y+cur_h+10), self.bg_color, -1)

            elif self.mood == 'curious':
                # Only "Curious" if looking far left or right
                if abs(self.x) > 20:
                    cut = 35 if (self.x > 0 and is_left) or (self.x < 0 and not is_left) else 0
                    cv2.rectangle(frame, (ex, mask_y-10), (ex+ew, mask_y+cut), self.bg_color, -1)

        # Draw execution
        if self.cyclops:
            draw_eye(cx - self.eye_w//2 + int(self.x), cy - self.eye_h//2 + int(self.y), 
                     self.eye_w, self.eye_h, self.eye_r, self.blink_l, True)
        else:
            # Left Eye
            draw_eye(cx - self.eye_spacing - self.l_eye_w + int(self.x), cy - self.l_eye_h//2 + int(self.y),
                     self.l_eye_w, self.l_eye_h, self.l_eye_r, self.blink_l, True)
            # Right Eye
            draw_eye(cx + self.eye_spacing + int(self.x), cy - self.r_eye_h//2 + int(self.y),
                     self.r_eye_w, self.r_eye_h, self.r_eye_r, self.blink_r, False)

# --- App Loop ---
def main():
    WIDTH, HEIGHT = 640, 480
    eyes = RoboEyes(WIDTH, HEIGHT)
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    print("Commands: [a]ngry, [h]appy, [s]cary, [c]urious, [d]efault, [w]ink, [y]cyclops")

    while True:
        eyes.update()
        eyes.draw(canvas)
        cv2.imshow("RoboEyes Port", canvas)
        
        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'): break
        elif key == ord('a'): eyes.set_mood('angry')
        elif key == ord('h'): eyes.set_mood('happy')
        elif key == ord('s'): eyes.set_mood('scary')
        elif key == ord('c'): eyes.set_mood('curious')
        elif key == ord('d'): eyes.set_mood('default')
        elif key == ord('w'): eyes.wink(True)
        elif key == ord('y'): eyes.cyclops = not eyes.cyclops

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()