import cv2
import numpy as np
import time
import random

class RoboEyes:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.bg_color = (0, 0, 0)
        self.eye_color = (255, 190, 0)
        
        # --- Physical Dimensions ---
        self.eye_w, self.eye_h = 120, 130
        self.eye_r = 30
        self.eye_spacing = 50
        self.cyclops = False
        
        # Per-eye overrides
        self.l_eye_w, self.l_eye_h, self.l_eye_r = self.eye_w, self.eye_h, self.eye_r
        self.r_eye_w, self.r_eye_h, self.r_eye_r = self.eye_w, self.eye_h, self.eye_r

        # --- Movement & Animation State ---
        self.mood = 'default'
        self.x, self.y = 0.0, 0.0
        self.target_x, self.target_y = 0, 0
        self.blink_l, self.blink_r = 0.0, 0.0
        
        # Shake/Jitter offsets (for Laugh, Confuse, Flicker)
        self.off_x, self.off_y = 0, 0
        
        # Behavior Toggles
        self.auto_blink = True
        self.auto_idle = True
        self.hflicker = False  # Horizontal Flicker
        self.vflicker = False  # Vertical Flicker
        
        # Timers
        self.next_blink = time.time() + 2
        self.next_move = time.time() + 1
        self.last_flicker_time = 0

    def set_mood(self, mood): self.mood = mood.lower()

    def wink(self, is_right=True):
        if is_right: self.blink_r = 1.0
        else: self.blink_l = 1.0

    def update(self):
        now = time.time()
        self.off_x, self.off_y = 0, 0 # Reset jitters per frame

        # 1. Automatic Blinking
        if self.auto_blink and now > self.next_blink:
            self.blink_l = self.blink_r = 1.0
            self.next_blink = now + random.uniform(2, 6)
        
        # Smooth opening decay
        self.blink_l = max(0, self.blink_l - 0.12)
        self.blink_r = max(0, self.blink_r - 0.12)

        # 2. Automatic Idle Movement (Saccades)
        if self.auto_idle and now > self.next_move:
            self.target_x = random.randint(-60, 60)
            self.target_y = random.randint(-40, 40)
            self.next_move = now + random.uniform(0.5, 3.0)
        
        # Smooth interpolation to target
        self.x += (self.target_x - self.x) * 0.15
        self.y += (self.target_y - self.y) * 0.15

        # 3. Flicker Logic (High frequency jitter)
        if self.hflicker:
            self.off_x = random.randint(-15, 15)
        if self.vflicker:
            self.off_y = random.randint(-15, 15)

    def laugh(self):
        """Simulate a laughing jitter"""
        self.off_y = random.randint(-10, 0)
        self.set_mood('happy')

    def confuse(self):
        """Randomized eye sizes and positions"""
        self.off_x = random.randint(-10, 10)
        self.off_y = random.randint(-10, 10)
        self.set_mood('default')

    def draw(self, frame):
        frame[:] = self.bg_color
        cx, cy = self.width // 2, self.height // 2
        
        # Inner helper to draw eye and apply masks
        def draw_eye(ex, ey, ew, eh, er, blink_val, is_left):
            cur_h = int(eh * (1.0 - blink_val))
            y_off = (eh - cur_h) // 2
            final_y = ey + y_off + self.off_y
            final_x = ex + self.off_x
            
            # Base eye shape
            if cur_h > 4:
                r = min(er, ew // 2, cur_h // 2)
                cv2.rectangle(frame, (final_x + r, final_y), (final_x + ew - r, final_y + cur_h), self.eye_color, -1)
                cv2.rectangle(frame, (final_x, final_y + r), (final_x + ew, final_y + cur_h - r), self.eye_color, -1)
                for pt in [(final_x + r, final_y + r), (final_x + ew - r, final_y + r), 
                           (final_x + ew - r, final_y + cur_h - r), (final_x + r, final_y + cur_h - r)]:
                    cv2.circle(frame, pt, r, self.eye_color, -1)
            else:
                cv2.line(frame, (final_x, ey + eh // 2 + self.off_y), (final_x + ew, ey + eh // 2 + self.off_y), self.eye_color, 2)

            # Mood Masking (Cutting away from the white eye)
            if self.mood == 'angry':
                pts = [[final_x, final_y], [final_x + ew, final_y + 45], [final_x + ew, final_y - 60], [final_x, final_y - 60]] if is_left else \
                      [[final_x, final_y + 45], [final_x + ew, final_y], [final_x + ew, final_y - 60], [final_x, final_y - 60]]
                cv2.fillPoly(frame, [np.array(pts, np.int32)], self.bg_color)
            
            elif self.mood == 'happy':
                cv2.circle(frame, (final_x + ew // 2, final_y + cur_h + 40), ew, self.bg_color, -1)
            
            elif self.mood == 'tired':
                cv2.rectangle(frame, (final_x, final_y - 10), (final_x + ew, final_y + int(cur_h * 0.45)), self.bg_color, -1)

            elif self.mood == 'scary':
                cv2.rectangle(frame, (final_x, final_y - 10), (final_x + ew, final_y + 30), self.bg_color, -1)
                cv2.rectangle(frame, (final_x, final_y + cur_h - 30), (final_x + ew, final_y + cur_h + 10), self.bg_color, -1)

            elif self.mood == 'curious':
                # Curiosity triggers a squint on the eye looking 'away' from the movement
                if abs(self.x) > 25:
                    cut = 40 if (self.x > 0 and is_left) or (self.x < 0 and not is_left) else 0
                    cv2.rectangle(frame, (final_x, final_y - 10), (final_x + ew, final_y + cut), self.bg_color, -1)

            elif self.mood == 'frozen':
                # Frozen mood usually looks like static narrow slits
                cv2.rectangle(frame, (final_x, final_y - 10), (final_x + ew, final_y + int(cur_h * 0.3)), self.bg_color, -1)
                cv2.rectangle(frame, (final_x, final_y + int(cur_h * 0.7)), (final_x + ew, final_y + cur_h + 10), self.bg_color, -1)

        # Draw left and right eyes
        if self.cyclops:
            draw_eye(cx - self.eye_w // 2 + int(self.x), cy - self.eye_h // 2 + int(self.y), self.eye_w, self.eye_h, self.eye_r, self.blink_l, True)
        else:
            draw_eye(cx - self.eye_spacing - self.l_eye_w + int(self.x), cy - self.l_eye_h // 2 + int(self.y), self.l_eye_w, self.l_eye_h, self.l_eye_r, self.blink_l, True)
            draw_eye(cx + self.eye_spacing + int(self.x), cy - self.r_eye_h // 2 + int(self.y), self.r_eye_w, self.r_eye_h, self.r_eye_r, self.blink_r, False)

# --- Interactive Demo ---
def main():
    WIDTH, HEIGHT = 800, 600
    eyes = RoboEyes(WIDTH, HEIGHT)
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    print("--- Controls ---")
    print("Moods: [a]ngry, [h]appy, [s]cary, [c]urious, [t]ired, [f]rozen, [d]efault")
    print("Anims: [w]ink, [l]augh, [x]confuse")
    print("Toggles: [1] H-Flicker, [2] V-Flicker, [y] Cyclops")

    while True:
        eyes.update()
        eyes.draw(canvas)
        cv2.imshow("RoboEyes Full Port", canvas)
        
        key = cv2.waitKey(20) & 0xFF
        if key == ord('q'): break
        elif key == ord('a'): eyes.set_mood('angry')
        elif key == ord('h'): eyes.set_mood('happy')
        elif key == ord('s'): eyes.set_mood('scary')
        elif key == ord('c'): eyes.set_mood('curious')
        elif key == ord('t'): eyes.set_mood('tired')
        elif key == ord('f'): eyes.set_mood('frozen')
        elif key == ord('d'): eyes.set_mood('default')
        elif key == ord('w'): eyes.wink(True)
        elif key == ord('l'): eyes.laugh()
        elif key == ord('x'): eyes.confuse()
        elif key == ord('y'): eyes.cyclops = not eyes.cyclops
        elif key == ord('1'): eyes.hflicker = not eyes.hflicker
        elif key == ord('2'): eyes.vflicker = not eyes.vflicker

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()