// Designed for an Arduino Nano and PCA servo driver
// Centers all 12 quadruped servos on startup, then accepts manual serial commands

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "ServoConfig.h"

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

String readString = "";
int channel = 0;

void setup() {
  Serial.begin(9600);
  Serial.println("Initializing PWM Driver...");
  
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  // The Animos 35KG servo is a digital servo - theoretically can use 50-330Hz
  pwm.setPWMFreq(50);  // Analog servos run at ~50 Hz updates

  // Center all servos before allowing user input
  centerAllServos();

  Serial.println("----------------------------------");
  Serial.println("Servo Clocking Ready!");
  Serial.println("Type 'ch X' to set channel (e.g., 'ch 5').");
  Serial.println("Type a number to set angle or pulse.");
  Serial.println("----------------------------------");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();  //gets one byte from serial buffer
    readString += c;
    delay(2);
  }

  if (readString.length() > 0) {
    readString.trim();  // Remove any leading/trailing whitespace or newlines
    Serial.print("Received: ");
    Serial.println(readString);

    // Check if the string contains "ch"
    int chIndex = readString.indexOf("ch");
    if (chIndex >= 0) {
      // Find where the number starts (usually right after 'ch' + space)
      String channelPart = readString.substring(chIndex + 2);
      channel = channelPart.toInt();
      Serial.print("Channel changed to: ");
      Serial.println(channel);

      // Clear readString so it doesn't try to move a servo to "ch 5" degrees
      readString = "";
    } else {
      // No "ch" found, treat the input as a position value
      int n = readString.toInt();

      if (n >= 270) {
        Serial.print("Writing Microseconds to channel ");
        Serial.print(channel);
        Serial.print(": ");
        Serial.println(n);
        pwm.writeMicroseconds(channel, n);
      } else {
        Serial.print("Writing Angle to channel ");
        Serial.print(channel);
        Serial.print(": ");
        Serial.println(n);
        pwm.writeMicroseconds(channel, angleToPulse(n));
      }
      readString = "";
    }
  }
}

// Helper function to map angles to PWM pulses
int angleToPulse(int ang) {
  int pulse = map(ang, 0, 270, SERVO_MIN, SERVO_MAX);
  return pulse;
}

// Function to drive all servos to their configured centers
void centerAllServos() {
  Serial.println("Centering all servos to ServoConfig.h offsets...");
  
  // Front Left Leg
  pwm.writeMicroseconds(CH_FL_HIP, angleToPulse(FL_SERVO_CENTER_HIP));
  pwm.writeMicroseconds(CH_FL_FEMUR, angleToPulse(FL_SERVO_CENTER_FEMUR));
  pwm.writeMicroseconds(CH_FL_TIBIA, angleToPulse(FL_SERVO_CENTER_TIBIA));

  // Front Right Leg
  pwm.writeMicroseconds(CH_FR_HIP, angleToPulse(FR_SERVO_CENTER_HIP));
  pwm.writeMicroseconds(CH_FR_FEMUR, angleToPulse(FR_SERVO_CENTER_FEMUR));
  pwm.writeMicroseconds(CH_FR_TIBIA, angleToPulse(FR_SERVO_CENTER_TIBIA));

  // Back Left Leg
  pwm.writeMicroseconds(CH_BL_HIP, angleToPulse(BL_SERVO_CENTER_HIP));
  pwm.writeMicroseconds(CH_BL_FEMUR, angleToPulse(BL_SERVO_CENTER_FEMUR));
  pwm.writeMicroseconds(CH_BL_TIBIA, angleToPulse(BL_SERVO_CENTER_TIBIA));

  // Back Right Leg
  pwm.writeMicroseconds(CH_BR_HIP, angleToPulse(BR_SERVO_CENTER_HIP));
  pwm.writeMicroseconds(CH_BR_FEMUR, angleToPulse(BR_SERVO_CENTER_FEMUR));
  pwm.writeMicroseconds(CH_BR_TIBIA, angleToPulse(BR_SERVO_CENTER_TIBIA));

  Serial.println("All servos centered.");
}