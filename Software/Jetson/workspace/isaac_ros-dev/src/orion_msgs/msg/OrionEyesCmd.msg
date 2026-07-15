# --- Constants ---
uint8 MOOD_DEFAULT = 0
uint8 MOOD_HAPPY = 1
uint8 MOOD_CURIOUS = 2
uint8 MOOD_SLEEPING = 3

# --- Fields ---
uint8 mood
float32 gaze_x        # Horizontal gaze direction [-1.0, 1.0]
float32 gaze_y        # Vertical gaze direction [-1.0, 1.0]
bool power            # true = eyes on, false = eyes off
bool mood_changed     # true = mood was just updated this message (avoids re-setting same mood every tick)
bool auto_blink
bool auto_idle
float32 left_eye_scale   # 1.0 = normal, >1.0 = bigger (set by cmd_mux from motion)
float32 right_eye_scale  # 1.0 = normal, >1.0 = bigger (set by cmd_mux from motion)