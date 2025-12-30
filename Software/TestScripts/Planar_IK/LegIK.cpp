#include "LegIK.h"

LegIK::LegIK() {
  thetaHipServo = SERVO_CENTER_HIP;
  thetaFemurServo = SERVO_CENTER_FEMUR;
  thetaTibiaServo = SERVO_CENTER_TIBIA;
}

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
  thetaHipServo = SERVO_CENTER_HIP + toDegrees(theta1_rad);

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
  
  // Final Femur Servo Angle
  thetaFemurServo = SERVO_CENTER_FEMUR - toDegrees(theta2_rad);
  // Final Tibia Servo Angle
  float phi = toDegrees(theta3_rad) - THETA_TIBIA_OFFSET;
  float theta_s = 90 - phi + toDegrees(theta2_rad);
  thetaTibiaServo = SERVO_CENTER_TIBIA - theta_s; 

  return true;
}

float LegIK::getHipServoAngle() { return thetaHipServo; }
float LegIK::getFemurServoAngle() { return thetaFemurServo; }
float LegIK::getTibiaServoAngle() { return thetaTibiaServo; }

float LegIK::toDegrees(float rad) { return rad * 180.0 / PI; }
float LegIK::toRadians(float deg) { return deg * PI / 180.0; }