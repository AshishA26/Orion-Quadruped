import cv2
import numpy as np
import time
import random

class RoboEyes:
    def __init__(self, width, height, pixel_size=8):
        # We render to a tiny buffer and scale up to create 'blocks'
        self.pixel_size = pixel_size
        self.render_w = width // pixel_size
        self.render_h = height // pixel_size
        
        # Colors (OpenCV is BGR)
        self.bg_color = (0, 0, 0)
        self.eye_color = (255, 190, 0) # Vivid Blue (BGR: Blue=255, Green=190)
        
        # --- Physical Dimensions (Adjusted for small grid) ---
        self.eye_w, self.eye_h = 20, 22
        self.eye_r = 5
        self.eye_spacing = 8
        self.cyclops = False
        
        self.l_eye_w = self.r_eye_w = self.eye_w
        self.l_eye_h = self.r_eye_h = self.eye_h

        # --- States ---
        self.mood = 'default'
        self.x, self.y = 0.0, 0.0
        self.target_x, self.target_y = 0, 0
        self.blink_l, self.blink_r = 0.0, 0.0
        self.off_x, self.off_y = 0, 0
        
        self.auto_blink = True
        self.auto_idle = True
        self.hflicker = False
        self.vflicker = False
        
        self.next_blink = time.time() + 2
        self.next_move = time.time() + 1

    def set_mood(self, mood): self.mood = mood.lower()

    def update(self):
        now = time.time()
        self.off_x, self.off_y = 0, 0

        if self.auto_blink and now > self.next_blink:
            self.blink_l = self.blink_r = 1.0
            self.next_blink = now + random.uniform(2, 6)
        
        self.blink_l = max(0, self.blink_l - 0.2) # Faster snap for pixel look
        self.blink_r = max(0, self.blink_r - 0.2)

        if self.auto_idle and now > self.next_move:
            # Random movements restricted to the small grid
            self.target_x = random.randint(-10, 10)
            self.target_y = random.randint(-6, 6)
            self.next_move = now + random.uniform(0.5, 3.0)
        
        self.x += (self.target_x - self.x) * 0.2
        self.y += (self.target_y - self.y) * 0.2

        if self.hflicker: self.off_x = random.randint(-2, 2)
        if self.vflicker: self.off_y = random.randint(-2, 2)

    def draw(self):
        # Create small internal buffer
        buffer = np.zeros((self.render_h, self.render_w, 3), dtype=np.uint8)
        cx, cy = self.render_w // 2, self.render_h // 2
        
        def draw_eye(ex, ey, ew, eh, er, blink_val, is_left):
            cur_h = int(eh * (1.0 - blink_val))
            y_off = (eh - cur_h) // 2
            fx, fy = int(ex + self.off_x), int(ey + y_off + self.off_y)
            
            if cur_h > 1:
                r = min(er, ew // 2, cur_h // 2)
                # Rounded Rect components
                cv2.rectangle(buffer, (fx+r, fy), (fx+ew-r, fy+cur_h), self.eye_color, -1)
                cv2.rectangle(buffer, (fx, fy+r), (fx+ew, fy+cur_h-r), self.eye_color, -1)
                for pt in [(fx+r, fy+r), (fx+ew-r, fy+r), (fx+ew-r, fy+cur_h-r), (fx+r, fy+cur_h-r)]:
                    cv2.circle(buffer, pt, r, self.eye_color, -1)
            else:
                cv2.line(buffer, (fx, ey + eh // 2), (fx + ew, ey + eh // 2), self.eye_color, 1)

            # Mood Masks
            mask_y = fy
            if self.mood == 'angry':
                pts = [[fx, mask_y], [fx+ew, mask_y+6], [fx+ew, mask_y-10], [fx, mask_y-10]] if is_left else \
                      [[fx, mask_y+6], [fx+ew, mask_y], [fx+ew, mask_y-10], [fx, mask_y-10]]
                cv2.fillPoly(buffer, [np.array(pts, np.int32)], self.bg_color)
            elif self.mood == 'happy':
                cv2.circle(buffer, (fx+ew//2, mask_y+cur_h+12), ew, self.bg_color, -1)
            elif self.mood == 'scary':
                cv2.rectangle(buffer, (fx, mask_y-2), (fx+ew, mask_y+4), self.bg_color, -1)
                cv2.rectangle(buffer, (fx, mask_y+cur_h-4), (fx+ew, mask_y+cur_h+2), self.bg_color, -1)

        if self.cyclops:
            draw_eye(cx - self.eye_w//2 + self.x, cy - self.eye_h//2 + self.y, self.eye_w, self.eye_h, self.eye_r, self.blink_l, True)
        else:
            draw_eye(cx - self.eye_spacing - self.l_eye_w + self.x, cy - self.l_eye_h//2 + self.y, self.l_eye_w, self.l_eye_h, self.eye_r, self.blink_l, True)
            draw_eye(cx + self.eye_spacing + self.x, cy - self.r_eye_h//2 + self.y, self.r_eye_w, self.r_eye_h, self.eye_r, self.blink_r, False)

        # SCALE UP: Nearest Neighbor preserves the blocks
        return cv2.resize(buffer, (self.render_w * self.pixel_size, self.render_h * self.pixel_size), interpolation=cv2.INTER_NEAREST)

# --- Run ---
def main():
    W, H = 800, 600
    eyes = RoboEyes(W, H, pixel_size=5) # Change pixel_size to make blocks bigger/smaller
    
    while True:
        eyes.update()
        frame = eyes.draw()
        
        cv2.imshow("Jetson RoboEyes", frame)
        key = cv2.waitKey(20) & 0xFF
        if key == ord('q'): break
        elif key == ord('a'): eyes.set_mood('angry')
        elif key == ord('h'): eyes.set_mood('happy')
        elif key == ord('s'): eyes.set_mood('scary')
        elif key == ord('d'): eyes.set_mood('default')

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()