// Orientation and translation of the body (Body IK) to compute foot positions for all 4 legs

#include "BodyIK.h"

/**
 * Computes Body IK and updates all 4 legs
 * Params:
 * - transX Forward/Backward translation (mm)
 * - transY Left/Right translation (mm)
 * - transZ Up/Down translation (mm)
 * - roll   Rotation around X axis (radians)
 * - pitch  Rotation around Y axis (radians)
 * - yaw    Rotation around Z axis (radians)
 */
void updateBodyPosture(float transX, float transY, float transZ, float roll, float pitch, float yaw, float pivotX, float pivotY, float pivotZ) {
    // Trig values for the rotation matrix
    float cr = cosf(roll);  float sr = sinf(roll);
    float cp = cosf(pitch); float sp = sinf(pitch);
    float cy = cosf(yaw);   float sy = sinf(yaw);

    // Rotation Matrix Elements (Forward Rotation R)
    float ix =  cy * cp;
    float iy =  cy * sp * sr - sy * cr;
    float iz =  cy * sp * cr + sy * sr;

    float jx =  sy * cp;
    float jy =  sy * sp * sr + cr * cy;
    float jz =  sy * sp * cr - cy * sr;

    float kx = -sp;
    float ky =  cp * sr;
    float kz =  cp * cr;

    LegIK_t* legs[4] = {&legFrontLeft, &legFrontRight, &legBackLeft, &legBackRight};
    
    for (int i = 0; i < 4; i++) {
        LegIK_t* leg = legs[i];

        // Static Hip Offset (relative to COM)
        float hipX = leg->IS_FRONT_LEG ? (BODY_LENGTH_MM / 2.0f) : -(BODY_LENGTH_MM / 2.0f);
        float hipY = leg->IS_LEFT_LEG  ? (BODY_WIDTH_MM / 2.0f)  : -(BODY_WIDTH_MM / 2.0f);
        float hipZ = 0.0f;
        
        // Neutral Ground Point
        // Note: currentY (39.3mm) is used here as the default leg extension
        float footNeutralX = hipX;
        float footNeutralY = leg->IS_LEFT_LEG ? (hipY + L1_HIP) : (hipY - L1_HIP);
        float footNeutralZ = 160.0f; // Default standing height

        // Transform: Local = R^T * (Foot_Neutral - Pivot - Translation) + Pivot - Hip_Offset
        float dx = footNeutralX - pivotX - transX;
        float dy = footNeutralY - pivotY - transY;
        float dz = footNeutralZ - pivotZ - transZ;

        // Apply Transpose Rotation Matrix (R^T)
        float rotX = ix * dx + jx * dy + kx * dz;
        float rotY = iy * dx + jy * dy + ky * dz;
        float rotZ = iz * dx + jz * dy + kz * dz;

        // Result relative to the hip
        float localX = rotX + pivotX - hipX;
        float localY = rotY + pivotY - hipY;
        float localZ = rotZ + pivotZ - hipZ;

        // Convert to outward-facing Y for your specific IK
        float finalY = leg->IS_LEFT_LEG ? localY : -localY;

        updateLeg(leg, localX, finalY, localZ);
    }
}