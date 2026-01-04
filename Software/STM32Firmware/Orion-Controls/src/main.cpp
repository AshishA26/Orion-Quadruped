#include <Arduino.h>
#include <Adafruit_PWMServoDriver.h>
#include "LegIK.h"
#include "ServoConfig.h"

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

LegIK legFrontLeft(FL_SERVO_CENTER_HIP, FL_SERVO_CENTER_FEMUR, FL_SERVO_CENTER_TIBIA, CH_FL_HIP, CH_FL_FEMUR, CH_FL_TIBIA, true, true);
LegIK legFrontRight(FR_SERVO_CENTER_HIP, FR_SERVO_CENTER_FEMUR, FR_SERVO_CENTER_TIBIA, CH_FR_HIP, CH_FR_FEMUR, CH_FR_TIBIA, true, false);
LegIK legBackLeft(BL_SERVO_CENTER_HIP, BL_SERVO_CENTER_FEMUR, BL_SERVO_CENTER_TIBIA, CH_BL_HIP, CH_BL_FEMUR, CH_BL_TIBIA, false, true);
LegIK legBackRight(BR_SERVO_CENTER_HIP, BR_SERVO_CENTER_FEMUR, BR_SERVO_CENTER_TIBIA, CH_BR_HIP, CH_BR_FEMUR, CH_BR_TIBIA, false, false);

String readString = "";

// Default Home Position
float currentX = 0;
float currentY = 39.3; // L1, mm
float currentZ = 160; // Height of Dog, mm

// Function declarations
void stepGait();
void updateLeg(LegIK &leg, float, float, float);
void setServoAngle(int, float);

void setup() {
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(50); 
  
  // Move all legs to home position
  updateLeg(legFrontLeft, currentX, currentY, currentZ);
  updateLeg(legFrontRight, currentX, currentY, currentZ);
  updateLeg(legBackLeft, currentX, currentY, currentZ);
  updateLeg(legBackRight, currentX, currentY, currentZ);
  
  // Serial.begin(9600);
  // Serial.println("Inverse Kinematics Ready. Enter X value:");
}

void loop() {
  
  // Set Z position to commanded input position
  //  while (Serial.available()) {
  //   char c = Serial.read(); 
  //   readString += c;
  //   delay(2);
  // }
  // if (readString.length() > 0) {
  //   float newZ = readString.toFloat();
  //   Serial.print("Moving Z to: "); Serial.println(newZ);
  //   // Update X, keep Y and Z fixed at home position
  //   currentZ = newZ;
  //   updateLeg(currentX, currentY, currentZ);    
  //   readString = "";
  // } 
  
  // Horizontal motion
  // for(int i = -80; i < 80; i+=5){
  //   // Update X, keep Y and Z fixed at home position
  //   updateLeg(i, currentY, currentZ);
  // }
  // for(int i = 80; i > -80; i-=5){
  //   // Update X, keep Y and Z fixed at home position
  //   updateLeg(i, currentY, currentZ);
  // }

  // Veritical Motion
  // for(int i = 60; i < 180; i+=5){
  //   // Update Z, keep Y and X fixed at home position
  //   updateLeg(currentX, currentY, i);
  // }
  // for(int i = 180; i > 60; i-=5){
  //   // Update Z, keep Y and X fixed at home position
  //   updateLeg(currentX, currentY, i);
  // }
  
  // Gait pattern
  stepGait();
}

void stepGait() {
  int xMin = -80;
  int xMax = 80;
  int zBase = 180;    // "Ground" level
  int stepHeight = 60; // How high to lift (180 - 60 = 120 units of lift)
  
  // SWING PHASE: Move from Back (-80) to Front (80) in a semicircle
  // We use a float for 'i' to ensure smooth math for the sine wave
  for (float i = -80; i < 80; i += 2) {
    // Map the X position to a 0-180 degree range for the Sine wave
    float angle = ( (i - xMin) / (xMax - xMin) ) * PI;
    
    // Calculate Z: Start at base and subtract the sine offset
    int offsetZ = sin(angle) * stepHeight;
    int currentZ = zBase - offsetZ;
    
    updateLeg(legFrontLeft, i, currentY, currentZ);
    updateLeg(legFrontRight, i, currentY, currentZ);
    updateLeg(legBackLeft, i, currentY, currentZ);
    updateLeg(legBackRight, i, currentY, currentZ);
  }

  // STANCE PHASE: Move from Front (80) back to Back (-80) horizontally
  // This is the part where the robot actually pushes its body forward
  for (int i = 80; i > -80; i -= 2) {
    updateLeg(legFrontLeft, i, currentY, zBase); 
    updateLeg(legFrontRight, i, currentY, zBase);
    updateLeg(legBackLeft, i, currentY, zBase);
    updateLeg(legBackRight, i, currentY, zBase);
  }
}

void updateLeg(LegIK &leg, float x, float y, float z) {
  if (leg.calculate(x, y, z)) {
    float h = leg.getHipServoAngle();
    float f = leg.getFemurServoAngle();
    float t = leg.getTibiaServoAngle();
    setServoAngle(leg.getHipServoChannel(), h);
    setServoAngle(leg.getFemurServoChannel(), f);
    setServoAngle(leg.getTibiaServoChannel(), t);

    // Debug output
    // Serial.print(" Hip: "); Serial.print(h);
    // Serial.print(" Femur: "); Serial.print(f);
    // Serial.print(" Tibia: "); Serial.println(t);
    // delay(1);
  } else {
    // Serial.println("Error: Target out of reach.");
  }
}

void setServoAngle(int channel, float angle) {
  // Constraint for safety
  if (angle < 0) angle = 0;
  if (angle > 270) angle = 270;
  
  // Allow 2 decimal places in servo angle
  int pulse = map(angle * 100, 0, 27000, SERVO_MIN, SERVO_MAX);
  pwm.writeMicroseconds(channel, pulse);
}