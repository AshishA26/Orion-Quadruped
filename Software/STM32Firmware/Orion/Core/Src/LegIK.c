#include "LegIK.h"

// --- Helper Functions ---
static inline float toDegrees(float rad) { 
    return rad * 180.0f / M_PI; 
}

static inline float toRadians(float deg) { 
    return deg * M_PI / 180.0f; 
}

// --- Public Implementation ---

void LegIK_Init(LegIK_t *leg, float servoCenterHip, float servoCenterFemur, float servoCenterTibia, 
                int channelHip, int channelFemur, int channelTibia, 
                bool isFrontLeg, bool isLeftLeg) 
{
    leg->SERVO_CENTER_HIP = servoCenterHip;
    leg->SERVO_CENTER_FEMUR = servoCenterFemur;
    leg->SERVO_CENTER_TIBIA = servoCenterTibia;
    
    leg->CHANNEL_HIP = channelHip;
    leg->CHANNEL_FEMUR = channelFemur;
    leg->CHANNEL_TIBIA = channelTibia;
    
    leg->IS_FRONT_LEG = isFrontLeg;
    leg->IS_LEFT_LEG = isLeftLeg;
    
    leg->thetaHipServo_ = servoCenterHip;
    leg->thetaFemurServo_ = servoCenterFemur;
    leg->thetaTibiaServo_ = servoCenterTibia;
    
    leg->offset_hip = 0.0f;
}

bool LegIK_Calculate(LegIK_t *leg, float x, float y, float z) 
{
    // --- Hip Calculation ---
    // TODO: need to revisit eqns for hip....
    // Solve for the length D in the hip plane
    // D = sqrt(GivenY^2 + GivenZ^2 - L1^2) 
    float term1 = (y * y) + (z * z) - (L1_HIP * L1_HIP);
    if (term1 < 0.0f) {
        return false; // Impossible geometry
    }
    float D = sqrtf(term1);
    
    // Calculate virtual Hip Angle
    // Note: atan2(y, z) handles the quadrant logic better than atan(y/z)
    // Note: Subtract the L1 offset angle so straight down equals 0 degrees
    float theta1_rad = atan2f(y, z) - atan2f(L1_HIP, D); 
    
    // Final Hip Servo Angle
    if (leg->IS_LEFT_LEG) { // Left/right symmetry
        leg->thetaHipServo_ = leg->SERVO_CENTER_HIP + toDegrees(theta1_rad);
        leg->offset_hip = leg->SERVO_CENTER_HIP + 4.0f;
    } else {
        // For rear legs Hip servo moves in the oppsite direction
        leg->thetaHipServo_ = leg->SERVO_CENTER_HIP - toDegrees(theta1_rad);
        leg->offset_hip = leg->SERVO_CENTER_HIP - 4.0f;
    }

    // --- Leg Plane (Femur & Tibia) ---
    // D is now the desired vertical distance in the leg-plane
    float G = sqrtf((D * D) + (x * x));
    if (G > (L2_FEMUR + L3_TIBIA)) {
        return false; // Target out of reach
    }

    // Solve Theta 3 (Tibia/Knee)
    float numerator = (G * G) - (L2_FEMUR * L2_FEMUR) - (L3_TIBIA * L3_TIBIA);
    float denominator = -2.0f * L2_FEMUR * L3_TIBIA;
    float theta3_rad = acosf(numerator / denominator);

    // Solve Theta 2 (Femur) 
    float alpha_femur = atan2f(x, D);
    float beta_femur = asinf((L3_TIBIA * sinf(theta3_rad)) / G);
    float theta2_rad = toRadians(90.0f) - (beta_femur - alpha_femur); // TODO: will this reference to 90 deg cause issues if moving femur above horizontal?
    
    // Accounting for Tibia servo offset and femur coupling
    float phi = toDegrees(theta3_rad) - THETA_TIBIA_OFFSET;
    float theta_s = 90.0f - phi + toDegrees(theta2_rad);
    
    // Final Femur and Tibia Servo Angles
    if (leg->IS_LEFT_LEG) {
        leg->thetaFemurServo_ = leg->SERVO_CENTER_FEMUR - toDegrees(theta2_rad);
        leg->thetaTibiaServo_ = leg->SERVO_CENTER_TIBIA - theta_s; 
    } else {
        // For right legs femur and tibia servo moves in the oppsite direction
        leg->thetaFemurServo_ = leg->SERVO_CENTER_FEMUR + toDegrees(theta2_rad);
        leg->thetaTibiaServo_ = leg->SERVO_CENTER_TIBIA + theta_s; 
    }
    
    return true;
}

int LegIK_GetHipServoChannel(LegIK_t *leg) { return leg->CHANNEL_HIP; }
int LegIK_GetFemurServoChannel(LegIK_t *leg) { return leg->CHANNEL_FEMUR; }
int LegIK_GetTibiaServoChannel(LegIK_t *leg) { return leg->CHANNEL_TIBIA; }

float LegIK_GetHipServoAngle(LegIK_t *leg) { return leg->thetaHipServo_; }
float LegIK_GetFemurServoAngle(LegIK_t *leg) { return leg->thetaFemurServo_; }
float LegIK_GetTibiaServoAngle(LegIK_t *leg) { return leg->thetaTibiaServo_; }