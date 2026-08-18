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
    // leg->offset_hip = 0.0f;

    // Joint angle tracking variables (does not set anything, just to send to jetson)
    leg->jointAngleHip_ = 0;
    leg->jointAngleTibia_ = 0;
    leg->jointAngleFemur_ = 0;
}

bool LegIK_Calculate(LegIK_t *leg, float x, float y, float z) 
{
    // --- Hip Calculation ---
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
    if (leg->IS_LEFT_LEG) {
        if (leg->IS_FRONT_LEG) {
            leg->thetaHipServo_ = leg->SERVO_CENTER_HIP + toDegrees(theta1_rad);
        } else {
            leg->thetaHipServo_ = leg->SERVO_CENTER_HIP - toDegrees(theta1_rad);
        }
        // leg->offset_hip = leg->SERVO_CENTER_HIP + 4.0f;
    } else {
        if (leg->IS_FRONT_LEG) {
            leg->thetaHipServo_ = leg->SERVO_CENTER_HIP - toDegrees(theta1_rad);
        } else {
            leg->thetaHipServo_ = leg->SERVO_CENTER_HIP + toDegrees(theta1_rad);
        }
        // leg->offset_hip = leg->SERVO_CENTER_HIP - 4.0f;
    }

    // --- Leg Plane (Femur & Tibia) ---
    // D is now the desired vertical distance in the leg-plane
    float G = sqrtf((D * D) + (x * x));
    // Clamp out-of-reach coordinates instead of failing
    float max_reach = L2_FEMUR + L3_TIBIA - 0.1f; // 0.1mm epsilon for float safety
    if (G > max_reach) {
        float scale = max_reach / G;
        x *= scale;
        D *= scale;
        G = max_reach;
    }

    // Solve Theta 3 (Tibia/Knee)
    float numerator = (G * G) - (L2_FEMUR * L2_FEMUR) - (L3_TIBIA * L3_TIBIA);
    float denominator = -2.0f * L2_FEMUR * L3_TIBIA;
    float cos_angle3 = numerator / denominator;
    cos_angle3 = fmaxf(-1.0f, fminf(1.0f, cos_angle3)); // Clamp between -1.0 and 1.0
    float theta3_rad = acosf(cos_angle3);

    // Solve Theta 2 (Femur) 
    float alpha_femur = atan2f(x, D);
    float sin_angle2 = (L3_TIBIA * sinf(theta3_rad)) / G;
    sin_angle2 = fmaxf(-1.0f, fminf(1.0f, sin_angle2)); // Clamp between -1.0 and 1.0
    float beta_femur = asinf(sin_angle2);
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

    float hipJoint_deg, femurJoint_deg, tibiaJoint_deg;

    // Mirror using the SAME left/right, front/back logic as the servo hip angle,
    // but with no SERVO_CENTER offset — this needs to match sign convention of
    // each leg's URDF axis, so treat the signs below as a starting point and
    // verify/flip per-joint using the calibration procedure below.
    if (leg->IS_LEFT_LEG) {
        hipJoint_deg = leg->IS_FRONT_LEG ?  toDegrees(theta1_rad) : -toDegrees(theta1_rad);
        femurJoint_deg = -toDegrees(theta2_rad);
        tibiaJoint_deg = -(toDegrees(theta3_rad) - 180.0f);
    } else {
        hipJoint_deg = leg->IS_FRONT_LEG ? -toDegrees(theta1_rad) :  toDegrees(theta1_rad);
        femurJoint_deg =  toDegrees(theta2_rad);
        tibiaJoint_deg =  (toDegrees(theta3_rad) - 180.0f);
    }

    leg->jointAngleHip_   = hipJoint_deg;
    leg->jointAngleFemur_ = femurJoint_deg;
    leg->jointAngleTibia_ = tibiaJoint_deg;

    return true;
}

int LegIK_GetHipServoChannel(LegIK_t *leg) { return leg->CHANNEL_HIP; }
int LegIK_GetFemurServoChannel(LegIK_t *leg) { return leg->CHANNEL_FEMUR; }
int LegIK_GetTibiaServoChannel(LegIK_t *leg) { return leg->CHANNEL_TIBIA; }

float LegIK_GetHipServoAngle(LegIK_t *leg) { return leg->thetaHipServo_; }
float LegIK_GetFemurServoAngle(LegIK_t *leg) { return leg->thetaFemurServo_; }
float LegIK_GetTibiaServoAngle(LegIK_t *leg) { return leg->thetaTibiaServo_; }

float LegIK_GetHipJointAngle(LegIK_t *leg) { return leg->jointAngleHip_; }
float LegIK_GetFemurJointAngle(LegIK_t *leg) { return leg->jointAngleFemur_; }
float LegIK_GetTibiaJointAngle(LegIK_t *leg) { return leg->jointAngleTibia_; }