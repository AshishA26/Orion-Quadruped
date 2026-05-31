#include "LegMotion.h"

/* Global Leg Objects */
LegIK_t legFrontLeft;
LegIK_t legFrontRight;
LegIK_t legBackLeft;
LegIK_t legBackRight;

float currentX = 0;
float currentY = 39.3f; // L1, mm
float currentZ = 160.0f; // Height of Dog, mm

// Global phase clock for continuous gaits (0.0 to 1.0)
static float gait_phase = 0.0f;

static long map(long x, long in_min, long in_max, long out_min, long out_max);
static int angleToPulse(int ang);
static void setServoAngle(int channel, float angle);

// Interpolation function to map angles to pulse widths
static long map(long x, long in_min, long in_max, long out_min, long out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// Helper function to map angles to PWM pulses
static int angleToPulse(int ang) {
  int pulse = map(ang, 0, 270, SERVO_MIN, SERVO_MAX);
  return pulse;
}

// Initialize all legs
void LegIK_HardwareInit(void) {
    LegIK_Init(&legFrontLeft, FL_SERVO_CENTER_HIP, FL_SERVO_CENTER_FEMUR, FL_SERVO_CENTER_TIBIA, CH_FL_HIP, CH_FL_FEMUR, CH_FL_TIBIA, true, true);
    LegIK_Init(&legFrontRight, FR_SERVO_CENTER_HIP, FR_SERVO_CENTER_FEMUR, FR_SERVO_CENTER_TIBIA, CH_FR_HIP, CH_FR_FEMUR, CH_FR_TIBIA, true, false);
    LegIK_Init(&legBackLeft, BL_SERVO_CENTER_HIP, BL_SERVO_CENTER_FEMUR, BL_SERVO_CENTER_TIBIA, CH_BL_HIP, CH_BL_FEMUR, CH_BL_TIBIA, false, true);
    LegIK_Init(&legBackRight, BR_SERVO_CENTER_HIP, BR_SERVO_CENTER_FEMUR, BR_SERVO_CENTER_TIBIA, CH_BR_HIP, CH_BR_FEMUR, CH_BR_TIBIA, false, false);
}

static void setServoAngle(int channel, float angle) {
  // Constraint for safety
  if (angle < 0.0f) angle = 0.0f;
  if (angle > 270.0f) angle = 270.0f;
  
  // Create mapping with extra precision to reduce integer float rounding loss
  long pulse = map((long)(angle * 100.0f), 0, 27000, SERVO_MIN, SERVO_MAX);
  PCA9685_WriteMicroseconds((uint8_t)channel, (uint16_t)pulse);
}

void updateLeg(LegIK_t *leg, float x, float y, float z) {
  if (LegIK_Calculate(leg, x, y, z)) {
    float h = LegIK_GetHipServoAngle(leg);
    float f = LegIK_GetFemurServoAngle(leg);
    float t = LegIK_GetTibiaServoAngle(leg);
    setServoAngle(LegIK_GetHipServoChannel(leg), h);
    setServoAngle(LegIK_GetFemurServoChannel(leg), f);
    setServoAngle(LegIK_GetTibiaServoChannel(leg), t);
  }
}

void standingPose(void) {
    float back_x = 0;
    float front_x = 0;
    float back_z = 160;
    float front_z = 160;
    float y = currentY; // The leg equations use absolute Y

    updateLeg(&legFrontLeft, front_x, y, front_z);
    updateLeg(&legFrontRight, front_x, y, front_z);
    updateLeg(&legBackLeft, back_x, y, back_z);
    updateLeg(&legBackRight, back_x, y, back_z);
}

void crouchingPose(void) {
    float back_x = 0;
    float front_x = 0;
    float back_z = 100;
    float front_z = 100;
    float y = currentY; 

    updateLeg(&legFrontLeft, front_x, y, front_z);
    updateLeg(&legFrontRight, front_x, y, front_z);
    updateLeg(&legBackLeft, back_x, y, back_z);
    updateLeg(&legBackRight, back_x, y, back_z);
}

void heelingPose(void) {
    float back_x = -20;
    float front_x = -20;
    float back_z = 120;
    float front_z = 180;
    float y = currentY; 

    updateLeg(&legFrontLeft, front_x, y, front_z);
    updateLeg(&legFrontRight, front_x, y, front_z);
    updateLeg(&legBackLeft, back_x, y, back_z);
    updateLeg(&legBackRight, back_x, y, back_z);
}

void unisonGait(void) {
  const int Z_BASE = 180;    
  const int STEP_HEIGHT = 60; 
  const int INTERPOLATION_INCREMENT = 2;
  const int GAIT_X_MAX = 80;
  const int GAIT_X_MIN = -80;
  
  // SWING PHASE
  for (float i = GAIT_X_MIN; i < GAIT_X_MAX; i += INTERPOLATION_INCREMENT) {
    float angle = ( (i - GAIT_X_MIN) / (GAIT_X_MAX - GAIT_X_MIN) ) * 3.14159f;
    int offsetZ = sinf(angle) * STEP_HEIGHT;
    int curZ = Z_BASE - offsetZ;
    updateLeg(&legFrontLeft, i, currentY, curZ);
    updateLeg(&legFrontRight, i, currentY, curZ);
    updateLeg(&legBackLeft, i, currentY, curZ);
    updateLeg(&legBackRight, i, currentY, curZ);
    osDelay(10); // Added small task yield for gait speed
  }

  // STANCE PHASE
  for (int i = GAIT_X_MAX; i > GAIT_X_MIN; i -= INTERPOLATION_INCREMENT) {
    updateLeg(&legFrontLeft, i, currentY, Z_BASE); 
    updateLeg(&legFrontRight, i, currentY, Z_BASE);
    updateLeg(&legBackLeft, i, currentY, Z_BASE);
    updateLeg(&legBackRight, i, currentY, Z_BASE);
    osDelay(10);
  }
}

void stepGait(void) {
  const int Z_BASE = 180;    
  const int STEP_HEIGHT = 50; 
  const int INTERPOLATION_INCREMENT = 2; 
  const int GAIT_X_MAX = 20;
  const int GAIT_X_MIN = -20;
  const float TOTAL_X_DIST = GAIT_X_MAX - GAIT_X_MIN;

  // --- HALF CYCLE 1 ---
  for (float i = GAIT_X_MIN; i <= GAIT_X_MAX; i += INTERPOLATION_INCREMENT) {
    float progress = (i - GAIT_X_MIN) / TOTAL_X_DIST; 
    float angle = progress * 3.14159f; 
    int offsetZ = sinf(angle) * STEP_HEIGHT;
    int swingZ = Z_BASE - offsetZ;
    float swingX = i; 
    
    float stanceX = GAIT_X_MAX - (i - GAIT_X_MIN); 
    int stanceZ = Z_BASE;

    updateLeg(&legFrontRight, stanceX, currentY, stanceZ);
    updateLeg(&legBackLeft, stanceX, currentY, stanceZ);
    updateLeg(&legFrontLeft, swingX, currentY, swingZ);
    updateLeg(&legBackRight, swingX, currentY, swingZ);
    osDelay(15);
  }

  // --- HALF CYCLE 2 ---
  for (float i = GAIT_X_MIN; i <= GAIT_X_MAX; i += INTERPOLATION_INCREMENT) {
    float progress = (i - GAIT_X_MIN) / TOTAL_X_DIST;
    float angle = progress * 3.14159f;
    int offsetZ = sinf(angle) * STEP_HEIGHT;
    int swingZ = Z_BASE - offsetZ;
    float swingX = i;
    
    float stanceX = GAIT_X_MAX - (i - GAIT_X_MIN);
    int stanceZ = Z_BASE;
    
    updateLeg(&legFrontRight, swingX, currentY, swingZ);
    updateLeg(&legBackLeft, swingX, currentY, swingZ);
    updateLeg(&legFrontLeft, stanceX, currentY, stanceZ);
    updateLeg(&legBackRight, stanceX, currentY, stanceZ);
    osDelay(15);
  }
}

void sineStepGait(void) {
  const int Z_BASE = 180;        
  const int STEP_HEIGHT = 50;    
  const int STANCE_DEPTH = 15;   
  const int INTERPOLATION_INCREMENT = 2; 
  const int GAIT_X_MAX = 20;
  const int GAIT_X_MIN = -20;
  const float TOTAL_X_DIST = GAIT_X_MAX - GAIT_X_MIN;

  // --- HALF CYCLE 1 ---
  for (float i = GAIT_X_MIN; i <= GAIT_X_MAX; i += INTERPOLATION_INCREMENT) {
    float progress = (i - GAIT_X_MIN) / TOTAL_X_DIST; 
    float angle = progress * 3.14159f; 
    
    int swingZ = Z_BASE - (sinf(angle) * STEP_HEIGHT);
    float swingX = i; 
    
    int stanceZ = Z_BASE + (sinf(angle) * STANCE_DEPTH);
    float stanceX = GAIT_X_MAX - (i - GAIT_X_MIN); 

    updateLeg(&legFrontRight, stanceX, currentY, stanceZ);
    updateLeg(&legBackLeft, stanceX, currentY, stanceZ);
    updateLeg(&legFrontLeft, swingX, currentY, swingZ);
    updateLeg(&legBackRight, swingX, currentY, swingZ);
    osDelay(10); 
  }

  // --- HALF CYCLE 2 ---
  for (float i = GAIT_X_MIN; i <= GAIT_X_MAX; i += INTERPOLATION_INCREMENT) {
    float progress = (i - GAIT_X_MIN) / TOTAL_X_DIST;
    float angle = progress * 3.14159f;
    
    int swingZ = Z_BASE - (sinf(angle) * STEP_HEIGHT);
    float swingX = i;
    
    int stanceZ = Z_BASE + (sinf(angle) * STANCE_DEPTH);
    float stanceX = GAIT_X_MAX - (i - GAIT_X_MIN);
    
    updateLeg(&legFrontRight, swingX, currentY, swingZ);
    updateLeg(&legBackLeft, swingX, currentY, swingZ);
    updateLeg(&legFrontLeft, stanceX, currentY, stanceZ);
    updateLeg(&legBackRight, stanceX, currentY, stanceZ);
    osDelay(10);
  }
}

void waveFrontRightLeg(void) {
  float front_x = 0;
  float current_z = currentZ;
  float y = currentY;

  // Make both back legs to crouch down, with the back-left going down the most.
  for (int i = 0; i <= 20; i++) {
    float ratio = i / 20.0f; // Ratio used for interpolation (0.0 to 1.0)
    float shiftZ = 25.0f * ratio;  // Drop the whole body down by 25mm
    float shiftX = -40.0f * ratio; // Shift center of mass backwards
    float shiftY = 20.0f * ratio;  // Shift center of mass leftwards
    
    float pitch = 0.20f * ratio;   // Pitch frontside upwards
    float roll = 0.15f * ratio;    // Roll rightside upwards
    
    updateBodyPosture(shiftX, shiftY, shiftZ, roll, pitch, 0.0f, 0.0f, 0.0f, 0.0f);
    osDelay(20);
  }

  // Lift the front right leg and bring it out
  const float LIFT_Z = 80;
  const float STRETCH_X = 60; // Reach forward
  const float STRETCH_Y = y + 60; // Reach outwards
  
  // Move front right leg to the "out" position
  for (int i = 0; i <= 20; i++) {
    float ratio = i / 20.0f;
    float current_leg_z = current_z - (ratio * (current_z - LIFT_Z));
    float current_leg_x = front_x + (ratio * (STRETCH_X - front_x));
    float current_leg_y = y + (ratio * (STRETCH_Y - y));
    
    updateLeg(&legFrontRight, current_leg_x, current_leg_y, current_leg_z);
    osDelay(20);
  }
  
  // Wiggle the tibia back and forth
  float base_tibia = LegIK_GetTibiaServoAngle(&legFrontRight);
  for (int w = 0; w < 4; w++) {
    for(int i = 0; i <= 15; i++) {
        setServoAngle(CH_FR_TIBIA, base_tibia - 45.0f * (i/15.0f));
        osDelay(10);
    }
    for(int i = 15; i >= 0; i--) {
        setServoAngle(CH_FR_TIBIA, base_tibia - 45.0f * (i/15.0f));
        osDelay(10);
    }
  }
  
  // Bring it back from the "out" position
  for (int i = 20; i >= 0; i--) {
    float ratio = i / 20.0f;
    float current_leg_z = current_z - (ratio * (current_z - LIFT_Z));
    float current_leg_x = front_x + (ratio * (STRETCH_X - front_x));
    float current_leg_y = y + (ratio * (STRETCH_Y - y));
    
    updateLeg(&legFrontRight, current_leg_x, current_leg_y, current_leg_z);
    osDelay(20);
  }
  
  // Restore weight distribution
  for (int i = 20; i >= 0; i--) {
    float ratio = i / 20.0f;
    float shiftZ = 25.0f * ratio;
    float shiftX = -40.0f * ratio; 
    float shiftY = 20.0f * ratio;
    float pitch = 0.20f * ratio;
    float roll = 0.15f * ratio;
    updateBodyPosture(shiftX, shiftY, shiftZ, roll, pitch, 0.0f, 0.0f, 0.0f, 0.0f);
    osDelay(20);
  }
}

// Function to drive all servos to their configured centers
void centerAllServos() {
  // Front Left Leg
  PCA9685_WriteMicroseconds(CH_FL_HIP, angleToPulse(FL_SERVO_CENTER_HIP));
  PCA9685_WriteMicroseconds(CH_FL_FEMUR, angleToPulse(FL_SERVO_CENTER_FEMUR));
  PCA9685_WriteMicroseconds(CH_FL_TIBIA, angleToPulse(FL_SERVO_CENTER_TIBIA));

  // Front Right Leg
  PCA9685_WriteMicroseconds(CH_FR_HIP, angleToPulse(FR_SERVO_CENTER_HIP));
  PCA9685_WriteMicroseconds(CH_FR_FEMUR, angleToPulse(FR_SERVO_CENTER_FEMUR));
  PCA9685_WriteMicroseconds(CH_FR_TIBIA, angleToPulse(FR_SERVO_CENTER_TIBIA));

  // Back Left Leg
  PCA9685_WriteMicroseconds(CH_BL_HIP, angleToPulse(BL_SERVO_CENTER_HIP));
  PCA9685_WriteMicroseconds(CH_BL_FEMUR, angleToPulse(BL_SERVO_CENTER_FEMUR));
  PCA9685_WriteMicroseconds(CH_BL_TIBIA, angleToPulse(BL_SERVO_CENTER_TIBIA));

  // Back Right Leg
  PCA9685_WriteMicroseconds(CH_BR_HIP, angleToPulse(BR_SERVO_CENTER_HIP));
  PCA9685_WriteMicroseconds(CH_BR_FEMUR, angleToPulse(BR_SERVO_CENTER_FEMUR));
  PCA9685_WriteMicroseconds(CH_BR_TIBIA, angleToPulse(BR_SERVO_CENTER_TIBIA));
}

void executeJoystickGait(float vel_x, float vel_y, float ang_z) {
    const float MAX_STRIDE_X = 60.0f; // Max mm forward/backward
    const float MAX_STRIDE_Y = 30.0f; // Max mm strafing side-to-side
    const float STEP_HEIGHT = 45.0f;  // Height of foot lift during swing
    const float BASE_Z = 160.0f;      // Default standing height
    
    // Check if joystick commands are effectively zero (deadband)
    float speed_magnitude = sqrtf(vel_x*vel_x + vel_y*vel_y);
    if (speed_magnitude < 0.05f && fabsf(ang_z) < 0.05f) {
        // Robot is stationary. Reset phase and stand still.
        gait_phase = 0.0f;
        standingPose();
        return;
    }

    // Increment global phase clock.
    // If speed is at max magnitude (1.0), it adds 0.04 per frame.
    // At 50Hz control loop (20ms), 0.04 * 50 = 2.0 cycles per second (Trot Gait)
    gait_phase += 0.04f * speed_magnitude;
    if (gait_phase >= 1.0f) gait_phase -= 1.0f;

    // Define the phase offsets for a Trot Gait (diagonal pairs move together)
    // Pair 1: Front Right & Back Left
    // Pair 2: Front Left & Back Right (offset by exactly half a cycle)
    float phase_FR = gait_phase;
    float phase_BL = gait_phase;
    
    float phase_FL = gait_phase + 0.5f;
    if (phase_FL >= 1.0f) phase_FL -= 1.0f;
    
    float phase_BR = phase_FL;

    // Helper arrays to process all 4 legs in one loop
    LegIK_t* legs[4] = {&legFrontRight, &legBackLeft, &legFrontLeft, &legBackRight};
    float phases[4]  = {phase_FR, phase_BL, phase_FL, phase_BR};
    
    // Dynamic strides based on joystick inputs
    float stride_x = MAX_STRIDE_X * vel_x;
    float stride_y = MAX_STRIDE_Y * vel_y;
    // float turning_bias = ang_z * ... (Turning omitted for simplicity in this basic translation gait)

    for (int i = 0; i < 4; i++) {
        float p = phases[i];
        float foot_x = 0;
        float foot_y = 0;
        float foot_z = BASE_Z;

        // Swing Phase (lifting and moving forward)
        // Happens during the first half of the phase clock (0.0 to 0.5)
        if (p < 0.5f) {
            float swing_progress = p / 0.5f; // Scale 0 to 0.5 up to 0 to 1.0
            
            // Linear travel from back to front
            // Start at -0.5*stride, end at +0.5*stride
            foot_x = - (stride_x * 0.5f) + (stride_x * swing_progress);
            foot_y = - (stride_y * 0.5f) + (stride_y * swing_progress);
            
            // Sine arc for height
            foot_z = BASE_Z - (sinf(swing_progress * 3.14159f) * STEP_HEIGHT);
        }
        // Stance Phase (foot on ground, pushing backward)
        // Happens during second half (0.5 to 1.0)
        else {
            float stance_progress = (p - 0.5f) / 0.5f; // Scale 0.5 to 1.0 up to 0 to 1.0
            
            // Linear travel from front back to back
            // Start at +0.5*stride, end at -0.5*stride
            foot_x = (stride_x * 0.5f) - (stride_x * stance_progress);
            foot_y = (stride_y * 0.5f) - (stride_y * stance_progress);
            
            // Z remains flat on the floor
            foot_z = BASE_Z;
        }

        // Update inverse kinematics
        // Note: The y-axis in LegIK operates on global absolute width (currentY), 
        // so we add the physical leg width to the calculated strafe delta.
        updateLeg(legs[i], foot_x, currentY + (legs[i]->IS_LEFT_LEG ? foot_y : -foot_y), foot_z);
    }
}