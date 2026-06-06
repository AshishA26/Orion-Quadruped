#ifndef __BODY_IK_H
#define __BODY_IK_H

#include <math.h>
#include "LegIK.h"
#include "LegMotion.h"

// --- Body Physical Dimensions ---
#define BODY_LENGTH_MM 248.5f  // Distance between front and back hip axes
#define BODY_WIDTH_MM  165.2f  // Distance between left and right hip axes

void updateBodyPosture(float transX, float transY, float transZ, float roll, float pitch, float yaw, float pivotX, float pivotY, float pivotZ);
void updateBodyPostureWithFeet(float footPositions[4][3], 
                               float transX, float transY, float transZ, 
                               float roll, float pitch, float yaw);

#endif // __BODY_IK_H