#include "LegIK.h"

LegIK::LegIK(float servoCenterHip, float servoCenterFemur, float servoCenterTibia, 
             int channelHip, int channelFemur, int channelTibia, 
             bool isFrontLeg, bool isLeftLeg) : 
  SERVO_CENTER_HIP(servoCenterHip), SERVO_CENTER_FEMUR(servoCenterFemur), SERVO_CENTER_TIBIA(servoCenterTibia),
  CHANNEL_HIP(channelHip), CHANNEL_FEMUR(channelFemur), CHANNEL_TIBIA(channelTibia),
  IS_FRONT_LEG(isFrontLeg), IS_LEFT_LEG(isLeftLeg),
  thetaHipServo_(servoCenterHip), thetaFemurServo_(servoCenterFemur), thetaTibiaServo_(servoCenterTibia)  {}

bool LegIK::calculate(float x, float y, float z) {
  // --- Hip Calculation ---
  // TODO: need to revisit eqns for hip....
  // Solve for the length D in the hip plane
  // D = sqrt(GivenY^2 + GivenZ^2 - L1^2) 
  float term1 = (y * y) + (z * z) - (L1_HIP * L1_HIP);
  if (term1 < 0) return false; // Impossible geometry
  float D = z;
  // Calculate virtual Hip Angle
  // Note: atan2(y, z) handles the quadrant logic better than atan(y/z)
  float theta1_rad = atan2(y, z); 
  // Final Hip Servo Angle
  if(IS_FRONT_LEG) {
    thetaHipServo_ = SERVO_CENTER_HIP + toDegrees(theta1_rad);
    offset_hip = SERVO_CENTER_HIP + 4;
  } else {
    // For rear legs Hip servo moves in the oppsite direction
    thetaHipServo_ = SERVO_CENTER_HIP - toDegrees(theta1_rad);
    offset_hip = SERVO_CENTER_HIP - 4;
  }

  // --- Leg Plane (Femur & Tibia) ---
  // D is now the desired vertical distance in the leg-plane
  float G = sqrt((D * D) + (x * x));
  if (G > (L2_FEMUR + L3_TIBIA)) return false; // Target out of reach

  // Solve Theta 3 (Tibia/Knee)
  float numerator = (G * G) - (L2_FEMUR * L2_FEMUR) - (L3_TIBIA * L3_TIBIA);
  float denominator = -2.0 * L2_FEMUR * L3_TIBIA;
  float theta3_rad = acos(numerator / denominator);

  // Solve Theta 2 (Femur) 
  float alpha_femur = atan2(x, D);
  float beta_femur = asin((L3_TIBIA * sin(theta3_rad)) / G);
  float theta2_rad = toRadians(90) - (beta_femur - alpha_femur); // TODO: will this reference to 90 deg cause issues if moving femur above horizontal?
  
  // Accounting for Tibia servo offset and femur coupling
  float phi = toDegrees(theta3_rad) - THETA_TIBIA_OFFSET;
  float theta_s = 90 - phi + toDegrees(theta2_rad);
  
  // Final Femur and Tibia Servo Angles
  if(IS_LEFT_LEG) {
    thetaFemurServo_ = SERVO_CENTER_FEMUR - toDegrees(theta2_rad);
    thetaTibiaServo_ = SERVO_CENTER_TIBIA - theta_s; 
  } else {
    // For right legs femur and tibia servo moves in the oppsite direction
    thetaFemurServo_ = SERVO_CENTER_FEMUR + toDegrees(theta2_rad);
    thetaTibiaServo_ = SERVO_CENTER_TIBIA + theta_s; 
  }
  return true;
}

int LegIK::getHipServoChannel() { return CHANNEL_HIP;}
int LegIK::getFemurServoChannel() { return CHANNEL_FEMUR;}
int LegIK::getTibiaServoChannel() { return CHANNEL_TIBIA;}

float LegIK::getHipServoAngle() { return offset_hip; } // thetaHipServo_;
float LegIK::getFemurServoAngle() { return thetaFemurServo_; }
float LegIK::getTibiaServoAngle() { return thetaTibiaServo_; }

float LegIK::toDegrees(float rad) { return rad * 180.0 / PI; }
float LegIK::toRadians(float deg) { return deg * PI / 180.0; }