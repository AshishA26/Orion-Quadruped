#ifndef LEGMOTION_H
#define LEGMOTION_H

#include "ServoConfig.h"
#include "LegIK.h"
#include <math.h>
#include "pca9685.h"
#include "cmsis_os.h"
#include "BodyIK.h"

extern LegIK_t legFrontLeft;
extern LegIK_t legFrontRight;
extern LegIK_t legBackLeft;
extern LegIK_t legBackRight;

extern float currentX;
extern float currentY;
extern float currentZ;

void updateLeg(LegIK_t *leg, float x, float y, float z);
void standingPose(void);
void crouchingPose(void);
void heelingPose(void);
void unisonGait(void);
void stepGait(void);
void sineStepGait(void);
void waveFrontRightLeg(void);
void LegIK_HardwareInit(void);
void centerAllServos(void);
void executeJoystickGait(float vel_x, float vel_y, float ang_z);
void calculateTrotGaitPositions(float vel_x, float vel_y, float ang_z, float outputFeet[4][3]);

#endif // LEGMOTION_H