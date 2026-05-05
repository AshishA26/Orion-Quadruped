// Orientation and translation (position) of the body (Body IK) to compute foot positions for all 4 legs

#include "BodyIK.h"

/**
 * Computes Body IK and updates all 4 legs
 * Params:
 * - transX  Forward/Backward translation (mm)
 * - transY  Left/Right translation (mm)
 * - transZ  Up/Down translation (mm)
 * - roll    Rotation around X axis (radians)
 * - pitch   Rotation around Y axis (radians)
 * - yaw     Rotation around Z axis (radians)
 * - pivotX/Y/Z  Center of Rotation (J_R)
 */
void updateBodyPosture(float transX, float transY, float transZ, float roll, float pitch, float yaw, float pivotX, float pivotY, float pivotZ) {
    // Trig values for the rotation matrix
    float cr = cosf(roll);  float sr = sinf(roll);
    float cp = cosf(pitch); float sp = sinf(pitch);
    float cy = cosf(yaw);   float sy = sinf(yaw);

    // Rotation Matrix Elements for R^-1
    // Since R is an orthogonal matrix, R^-1 is just the transpose (R^T)
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

        // --- DEFINING THE VECTORS FROM THE IMAGE ---

        // [CoM origin]: location of J1 relative to J0
        float comOriginX = leg->IS_FRONT_LEG ? (BODY_LENGTH_MM / 2.0f) : -(BODY_LENGTH_MM / 2.0f);
        float comOriginY = leg->IS_LEFT_LEG  ? (BODY_WIDTH_MM / 2.0f)  : -(BODY_WIDTH_MM / 2.0f);
        float comOriginZ = 0.0f;
        
        // [x, y, z]: location of foot, relative to J1 (Leg Origin)
        float footRelX = 0.0f;
        float footRelY = leg->IS_LEFT_LEG ? L1_HIP : -L1_HIP;
        float footRelZ = 160.0f; // Default standing height

        // --- STEP 1: New co-ord of feet relative to J0, center of Robot ---
        // Formula: XYZ_0 = R^-1 ( [CoM origin] + [x,y,z] - [Center of Rotation] )^T
        // Note: We subtract translation here to shift the robot's body in global space
        float vecX = comOriginX + footRelX - pivotX - transX;
        float vecY = comOriginY + footRelY - pivotY - transY;
        float vecZ = comOriginZ + footRelZ - pivotZ - transZ;

        // Apply R^-1 (Transpose Rotation Matrix)
        float XYZ_0_X = ix * vecX + jx * vecY + kx * vecZ;
        float XYZ_0_Y = iy * vecX + jy * vecY + ky * vecZ;
        float XYZ_0_Z = iz * vecX + jz * vecY + kz * vecZ;

        // --- STEP 2: New co-ord of feet relative to leg's origin ---
        // Formula: XYZ_1 = XYZ_0 - [CoM origin] + [Center of Rotation]
        float XYZ_1_X = XYZ_0_X - comOriginX + pivotX;
        float XYZ_1_Y = XYZ_0_Y - comOriginY + pivotY;
        float XYZ_1_Z = XYZ_0_Z - comOriginZ + pivotZ;

        // Convert to outward-facing Y for your specific IK solver
        float finalY = leg->IS_LEFT_LEG ? XYZ_1_Y : -XYZ_1_Y;

        // Use Inverse Kinematics on this
        updateLeg(leg, XYZ_1_X, finalY, XYZ_1_Z);
    }
}   