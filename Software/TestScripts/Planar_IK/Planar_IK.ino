// Designed for an Arduino Nano and PCA servo driver
// Implements Inverse Kinematics for a single leg

#include <Adafruit_PWMServoDriver.h>
#include "LegIK.h"

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
LegIK leg;

// Servo Limits
#define SERVO_MIN 500 
#define SERVO_MAX 2500 

// Servo Channels
#define CH_FEMUR 0
#define CH_TIBIA 1
#define CH_HIP   2

String readString = "";

// Default Home Position
float currentX = 0;
float currentY = 39.3; // L1, mm
float currentZ = 160; // Height of Dog, mm

void setup() {
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(50); 
  
  // Move to home position
  updateLeg(currentX, currentY, currentZ);
  
  Serial.begin(9600);
  Serial.println("Inverse Kinematics Ready. Enter X value:");
}

void loop() {
  
  //  while (Serial.available()) {
  //   char c = Serial.read(); 
  //   readString += c;
  //   delay(2);
  // }
  // if (readString.length() > 0) {
  //   float newX = readString.toFloat();
  //   Serial.print("Moving X to: "); Serial.println(newX);
    
  //   // Update X, keep Y and Z fixed at home position
  //   currentX = newX;
  //   updateLeg(currentX, currentY, currentZ);
    
  //   readString = "";
  // } 
  

  for(int i = -80; i < 80; i+=5){
    // Update X, keep Y and Z fixed at home position
    updateLeg(i, currentY, currentZ);
  }
  for(int i = 80; i > -80; i-=5){
    // Update X, keep Y and Z fixed at home position
    updateLeg(i, currentY, currentZ);
  }
  
}

void updateLeg(float x, float y, float z) {
  if (leg.calculate(x, y, z)) {
    float h = leg.getHipServoAngle();
    float f = leg.getFemurServoAngle();
    float t = leg.getTibiaServoAngle();

    // Debug output
    Serial.print(" Hip: "); Serial.print(h);
    Serial.print(" Femur: "); Serial.print(f);
    Serial.print(" Tibia: "); Serial.println(t);

    setServoAngle(CH_HIP, h);
    setServoAngle(CH_FEMUR, f);
    setServoAngle(CH_TIBIA, t);
  } else {
    Serial.println("Error: Target out of reach.");
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