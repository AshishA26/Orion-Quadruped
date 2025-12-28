// This program aims to find 0 position and bounds of a servo
// Originally designed for an Arduino Nano and PCA servo driver

#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// 0 to 270 degrees is 500 to 2500 microseconds
#define SERVO_MIN 500 
#define SERVO_MAX 2500 

void setup() {
  Serial.begin(9600);
  Serial.println("Servo Clocking. Ready!");
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  // The Animos 35KG servo is a digital servo - theoretically can use 50-330Hz
  pwm.setPWMFreq(50);  // Analog servos run at ~50 Hz updates
  pwm.writeMicroseconds(0, SERVO_MIN);
}

void loop() {
  // pwm.writeMicroseconds(0, SERVO_MIN);
  // delay(1000);
  // pwm.writeMicroseconds(0, (SERVO_MAX-SERVO_MIN)/2); // Theoretically, the middle position.
  // delay(1000);
  // pwm.writeMicroseconds(0, SERVO_MAX);
  // delay(1000);
  
  // // Sweep all servos from 0 to 270 degrees
  // float pos = SERVO_MIN;
  // // Forwards
  // for(float i = SERVO_MIN; i <= SERVO_MAX; i += 1) {
  //     pwm.writeMicroseconds(0, int(i));
  //     delayMicroseconds(2);
  // }
  // // Backwards
  // for(float i = SERVO_MAX; i <= SERVO_MIN; i -= 1) {
  //     pwm.writeMicroseconds(0, int(i));
  //     delayMicroseconds(2);
  // }

   while (Serial.available()) {
    char c = Serial.read();  //gets one byte from serial buffer
    readString += c; //makes the string readString
    delay(2);  //slow looping to allow buffer to fill with next character
  }

  if (readString.length() >0) {
    Serial.println(readString);  //so you can see the captured string 
    int n = readString.toInt();  //convert readString into a number

    if(n >= 270)
    {
      Serial.print("writing Microseconds: ");
      Serial.println(n);
      pwm.writeMicroseconds(0, n);
    }
    else
    {   
      Serial.print("writing Angle: ");
      Serial.println(n);
      pwm.writeMicroseconds(0, angleToPulse(n));
      myservo.write(n);
    }

    readString=""; //empty for next input
  } 
}

int angleToPulse(int ang) {
  int pulse = map(ang, 0, 270, SERVO_MIN, SERVO_MAX);
  Serial.print("Angle: "); Serial.print(ang);
  Serial.print(" Pulse: "); Serial.println(pulse);
  return pulse;
}