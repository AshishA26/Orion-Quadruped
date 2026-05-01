#ifndef LEGIK_H
#define LEGIK_H

#include <stdbool.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// --- Physical Limb Lengths (mm) ---
#define L1_HIP 39.3f
#define L2_FEMUR 109.50f
#define L3_TIBIA 119.90f

// --- Design offsets ---
#define THETA_TIBIA_OFFSET 5.88f // degrees

/**
 * @brief Struct to hold the state and configuration for a single Leg's IK
 */
typedef struct {
    float SERVO_CENTER_HIP;
    float SERVO_CENTER_FEMUR;
    float SERVO_CENTER_TIBIA;
    
    int CHANNEL_HIP;
    int CHANNEL_FEMUR;
    int CHANNEL_TIBIA;
    
    bool IS_FRONT_LEG;
    bool IS_LEFT_LEG;
    
    float thetaHipServo_;
    float thetaFemurServo_;
    float thetaTibiaServo_;
    float offset_hip;
} LegIK_t;

/**
 * @brief Initialize a LegIK_t structure
 */
void LegIK_Init(LegIK_t *leg, float servoCenterHip, float servoCenterFemur, float servoCenterTibia, 
                int channelHip, int channelFemur, int channelTibia, 
                bool isFrontLeg, bool isLeftLeg);

/**
 * @brief Calculates target angles for servo (0-270 range)
 * @retval true if position is reachable, false if not
 */
bool LegIK_Calculate(LegIK_t *leg, float x, float y, float z);

// Getters for the servo angles, accounting for alignment (in degrees)
float LegIK_GetHipServoAngle(LegIK_t *leg);
float LegIK_GetFemurServoAngle(LegIK_t *leg);
float LegIK_GetTibiaServoAngle(LegIK_t *leg);

// Getters for the servo channels
int LegIK_GetHipServoChannel(LegIK_t *leg);
int LegIK_GetFemurServoChannel(LegIK_t *leg);
int LegIK_GetTibiaServoChannel(LegIK_t *leg);

#endif // LEGIK_H