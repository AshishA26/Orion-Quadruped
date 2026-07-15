# --- Constants ---
uint8 CMD_NORMAL = 1
uint8 CMD_RESET = 2
uint8 CMD_WAVE = 3
uint8 CMD_HEEL = 4
uint8 CMD_DANCE = 5
uint8 CMD_EXTRAS = 6
uint8 CMD_EYES = 7

# --- Fields ---
uint8 cmd_type

# Walking velocities
float32 lin_x
float32 lin_y
float32 ang_z

# Posture
float32 roll
float32 pitch
float32 yaw
float32 z_offset
float32 yawing_direction

# Position offsets
float32 x_offset
float32 y_offset

# Pivot point
float32 pivot_x
float32 pivot_y