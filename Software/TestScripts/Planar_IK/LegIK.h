#ifndef LEGIK_H
#define LEGIK_H

#include <Arduino.h>
#include <math.h>

class LegIK {
  public:
    LegIK();
    
    // Calculates target angles for servo (0-270 range)
    // Returns true if position is reachable, false if not
    bool calculate(float x, float y, float z);

    // Getters for the servo angles, accounting for alignment (in degrees)
    float getHipServoAngle();
    float getFemurServoAngle();
    float getTibiaServoAngle();

  private:
    // Limb lengths    
    const float L1_HIP = 39.3;
    const float L2_FEMUR = 109.50; 
    const float L3_TIBIA = 119.90; 

    // Design offsets
    const float THETA_TIBIA_OFFSET = 5.88; // degrees
    // Servo Clocking Offsets, calibrated through clocking script
    const float SERVO_CENTER_HIP = 135.0;
    const float SERVO_CENTER_FEMUR = 75.0;
    const float SERVO_CENTER_TIBIA = 134.0;

    float thetaHipServo;
    float thetaFemurServo;
    float thetaTibiaServo;

    float toDegrees(float rad);
    float toRadians(float deg);
};

#endif