// This program moves the leg up and down in a straight vertical fashion

#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// 0 to 270 degrees is 500 to 2500 microseconds
#define SERVO_TOP_MIN 550 
#define SERVO_TOP_MAX 1100 
#define SERVO_BOTTOM_MIN 550
#define SERVO_BOTTOM_MAX 2500

void setup() {
  Serial.begin(9600);
  Serial.println("16 channel Servo test!");
  pwm.begin();

  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(50);  // Analog servos run at ~50 Hz updates
}

void loop() {
  // Set all servos to start
  pwm.writeMicroseconds(0, 900);
  pwm.writeMicroseconds(1, 1150);
  delay(1000);
  
  // Sweep all servos from 0 to 180 degrees
  float top_microsec = 900;
  float bot_microsec = 1150;

  // Set to 4 if wanting leg to jump, set to 1 for normal movement.
  increment = 4;
  for(float i = 0; i <= 350/increment; i += 1) {
      top_microsec-=increment;
      bot_microsec+=increment;
      pwm.writeMicroseconds(0, int(top_microsec));
      pwm.writeMicroseconds(1, int(bot_microsec));
      // Serial.print("Top ms: ");
      // Serial.print(top_microsec);
      // Serial.print("  Bottom ms: ");
      // Serial.print(bot_microsec);
      // Serial.println();
      delayMicroseconds(2);
  }
  for(float i = 0; i <= 350/increment; i += 1) {
      top_microsec+=increment;
      bot_microsec-=increment;
      pwm.writeMicroseconds(0, int(top_microsec));
      pwm.writeMicroseconds(1, int(bot_microsec));
      // Serial.print("Top ms: ");
      // Serial.print(top_microsec);
      // Serial.print("  Bottom ms: ");
      // Serial.print(bot_microsec);
      // Serial.println();
      delayMicroseconds(2);
  }
}

// int angleToPulse(int ang) {
//   int pulse = map(ang, 0, 270, SERVOMIN, SERVOMAX);
//   Serial.print("Angle: "); Serial.print(ang);
//   Serial.print(" pulse: "); Serial.println(pulse);
//   return pulse;
// }