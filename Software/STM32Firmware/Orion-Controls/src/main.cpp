#include <Arduino.h>



// // Designed for an Arduino Nano and PCA servo driver
// // Use this to find the 'middle position' and bounds of a servo

// #include <Adafruit_PWMServoDriver.h>

// Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// // 0 to 270 degrees is 500 to 2500 microseconds
// #define SERVO_MIN 500 
// #define SERVO_MAX 2500 
// String readString = "";

// int angleToPulse(int);

// void setup() {
//   Serial.begin(9600);
//   Serial.println("Servo Clocking. Ready!");
//   pwm.begin();
//   pwm.setOscillatorFrequency(27000000);
//   // The Animos 35KG servo is a digital servo - theoretically can use 50-330Hz
//   pwm.setPWMFreq(50);  // Analog servos run at ~50 Hz updates
//   pwm.writeMicroseconds(2, angleToPulse(135));
// }

// void loop() {
//    while (Serial.available()) {
//     char c = Serial.read();  //gets one byte from serial buffer
//     readString += c;
//     delay(2);
//   }

//   if (readString.length() >0) {
//     Serial.println(readString);
//     int n = readString.toInt();

//     if(n >= 270)
//     {
//       Serial.print("writing Microseconds: ");
//       Serial.println(n);
//       pwm.writeMicroseconds(2, n);
//     }
//     else
//     {   
//       Serial.print("writing Angle: ");
//       Serial.println(n);
//       pwm.writeMicroseconds(2, angleToPulse(n));
//     }

//     readString="";
//   } 
// }

// int angleToPulse(int ang) {
//   int pulse = map(ang, 0, 270, SERVO_MIN, SERVO_MAX);
//   Serial.print("Angle: "); Serial.print(ang);
//   Serial.print(" Pulse: "); Serial.println(pulse);
//   return pulse;
// }







#include <Adafruit_PWMServoDriver.h>
#include "LegIK.h"

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
LegIK leg;

// Servo Limits
#define SERVO_MIN 500 
#define SERVO_MAX 2500 

// Servo Channels
#define CH_FEMUR 1
#define CH_TIBIA 2
#define CH_HIP   0

String readString = "";

// Default Home Position
float currentX = 0;
float currentY = 39.3; // L1, mm
float currentZ = 160; // Height of Dog, mm

// Function declarations
void stepGait();
void updateLeg(float, float, float);
void setServoAngle(int, float);

void setup() {
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(50); 
  
  // Move to home position
  updateLeg(currentX, currentY, currentZ);
  
  // Serial.begin(9600);
  // Serial.println("Inverse Kinematics Ready. Enter X value:");
}

void loop() {
  
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
  
  // for(int i = -80; i < 80; i+=5){
  //   // Update X, keep Y and Z fixed at home position
  //   updateLeg(i, currentY, currentZ);
  // }
  // for(int i = 80; i > -80; i-=5){
  //   // Update X, keep Y and Z fixed at home position
  //   updateLeg(i, currentY, currentZ);
  // }

  // for(int i = 60; i < 180; i+=5){
  //   // Update X, keep Y and Z fixed at home position
  //   updateLeg(currentX, currentY, i);
  // }
  // for(int i = 180; i > 60; i-=5){
  //   // Update X, keep Y and Z fixed at home position
  //   updateLeg(currentX, currentY, i);
  // }
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
    
    updateLeg(i, currentY, currentZ);
  }

  // STANCE PHASE: Move from Front (80) back to Back (-80) horizontally
  // This is the part where the robot actually pushes its body forward
  for (int i = 80; i > -80; i -= 2) {
    updateLeg(i, currentY, zBase); 
  }
}

void updateLeg(float x, float y, float z) {
  if (leg.calculate(x, y, z)) {
    float h = leg.getHipServoAngle();
    float f = leg.getFemurServoAngle();
    float t = leg.getTibiaServoAngle();

    // Debug output
    // Serial.print(" Hip: "); Serial.print(h);
    // Serial.print(" Femur: "); Serial.print(f);
    // Serial.print(" Tibia: "); Serial.println(t);
    delay(5);

    setServoAngle(CH_HIP, h);
    setServoAngle(CH_FEMUR, f);
    setServoAngle(CH_TIBIA, t);
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