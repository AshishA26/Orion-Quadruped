# --- Constants ---
uint8 MOOD_DEFAULT = 0
uint8 MOOD_HAPPY = 1
uint8 MOOD_ANGRY = 2
uint8 MOOD_TIRED = 3
uint8 MOOD_CURIOUS = 4
uint8 MOOD_SCARY = 5

# --- Fields ---
uint8 mood
float32 gaze_x        # Horizontal gaze direction [-1.0, 1.0] (from strafing)
float32 gaze_y        # Vertical gaze direction [-1.0, 1.0] (reserved for future)
bool power            # true = eyes on, false = eyes off
bool mood_changed     # true = mood was just updated this message (avoids re-setting same mood every tick)