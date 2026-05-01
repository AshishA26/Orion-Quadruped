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
void updateBodyPosture(float transX, float transY, float transZ, float roll, float pitch, float yaw) {
    // 1. Trig values for the rotation matrix
    float cr = cosf(roll);  float sr = sinf(roll);
    float cp = cosf(pitch); float sp = sinf(pitch);
    float cy = cosf(yaw);   float sy = sinf(yaw);

    // 2. R^T (Body-Fixed Rotation Matrix)
    float r11 = cp * cy;
    float r12 = cp * sy;
    float r13 = -sp;
    float r21 = sr * sp * cy - cr * sy;
    float r22 = sr * sp * sy + cr * cy;
    float r23 = sr * cp;
    float r31 = cr * sp * cy + sr * sy;
    float r32 = cr * sp * sy - sr * cy;
    float r33 = cr * cp;

    LegIK_t* legs[4] = {&legFrontLeft, &legFrontRight, &legBackLeft, &legBackRight};
    
    for (int i = 0; i < 4; i++) {
        LegIK_t* leg = legs[i];

        // 3. Static Hip Offset (relative to COM)
        float hipX = leg->IS_FRONT_LEG ? (BODY_LENGTH_MM / 2.0f) : -(BODY_LENGTH_MM / 2.0f);
        float hipY = leg->IS_LEFT_LEG  ? (BODY_WIDTH_MM / 2.0f)  : -(BODY_WIDTH_MM / 2.0f);
        
        // 4. Neutral Ground Point[cite: 3, 8]
        // Note: currentY (39.3mm) is used here as the default leg extension[cite: 3]
        float footNeutralX = hipX;
        float footNeutralY = leg->IS_LEFT_LEG ? (hipY + L1_HIP) : (hipY - L1_HIP);
        float footNeutralZ = 160.0f; // Default standing height[cite: 3]

        // 5. Transform: Local = R^T * (Foot_Neutral - Translation) - Hip_Offset
        float dx = footNeutralX - transX;
        float dy = footNeutralY - transY;
        float dz = footNeutralZ - transZ;

        // Apply Rotation Matrix
        float rotX = r11 * dx + r12 * dy + r13 * dz;
        float rotY = r21 * dx + r22 * dy + r23 * dz;
        float rotZ = r31 * dx + r32 * dy + r33 * dz;

        // Subtract Hip Offset from the rotated vector
        float localX = rotX - hipX;
        float localY = rotY - hipY;
        float localZ = rotZ; // Assuming hip Z offset is 0 relative to COM

        // 6. Convert to outward-facing Y for your specific IK[cite: 2]
        float finalY = leg->IS_LEFT_LEG ? localY : -localY;

        updateLeg(leg, localX, finalY, localZ);
    }
}