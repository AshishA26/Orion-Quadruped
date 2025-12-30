// Designed for an Arduino Nano and PCA servo driver
// Use this to find the 'middle position' and bounds of a servo

#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// 0 to 270 degrees is 500 to 2500 microseconds
#define SERVO_MIN 500 
#define SERVO_MAX 2500 
String readString = "";

void setup() {
  Serial.begin(9600);
  Serial.println("Servo Clocking. Ready!");
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  // The Animos 35KG servo is a digital servo - theoretically can use 50-330Hz
  pwm.setPWMFreq(50);  // Analog servos run at ~50 Hz updates
  pwm.writeMicroseconds(1, angleToPulse(135));
}

void loop() {
   while (Serial.available()) {
    char c = Serial.read();  //gets one byte from serial buffer
    readString += c;
    delay(2);
  }

  if (readString.length() >0) {
    Serial.println(readString);
    int n = readString.toInt();

    if(n >= 270)
    {
      Serial.print("writing Microseconds: ");
      Serial.println(n);
      pwm.writeMicroseconds(1, n);
    }
    else
    {   
      Serial.print("writing Angle: ");
      Serial.println(n);
      pwm.writeMicroseconds(1, angleToPulse(n));
    }

    readString="";
  } 
}

int angleToPulse(int ang) {
  int pulse = map(ang, 0, 270, SERVO_MIN, SERVO_MAX);
  Serial.print("Angle: "); Serial.print(ang);
  Serial.print(" Pulse: "); Serial.println(pulse);
  return pulse;
}