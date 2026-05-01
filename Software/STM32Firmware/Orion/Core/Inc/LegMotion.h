#ifndef LEGMOTION_H
#define LEGMOTION_H

#include "ServoConfig.h"
#include "LegIK.h"
#include <math.h>
#include "pca9685.h"
#include "cmsis_os.h"

void standingPose(void);
void crouchingPose(void);
void heelingPose(void);
void unisonGait(void);
void stepGait(void);
void sineStepGait(void);
void LegIK_HardwareInit(void);
void centerAllServos(void);

#endif // LEGMOTION_H