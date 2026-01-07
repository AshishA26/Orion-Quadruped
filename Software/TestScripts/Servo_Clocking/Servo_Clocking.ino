// Designed for an Arduino Nano and PCA servo driver
// Use this to find the 'middle position' and bounds of a servo

#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// 0 to 270 degrees is 500 to 2500 microseconds
#define SERVO_MIN 500 
#define SERVO_MAX 2500 
String readString = "";
int channel = 0;

void setup() {
  Serial.begin(9600);
  Serial.println("Servo Clocking. Ready!");
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  // The Animos 35KG servo is a digital servo - theoretically can use 50-330Hz
  pwm.setPWMFreq(50);  // Analog servos run at ~50 Hz updates
  // pwm.writeMicroseconds(1, angleToPulse(135));
}

void loop() {
   while (Serial.available()) {
    char c = Serial.read();  //gets one byte from serial buffer
    readString += c;
    delay(2);
  }

  if (readString.length() > 0) {
    readString.trim(); // Remove any leading/trailing whitespace or newlines
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
    } 
    else {
      // No "ch" found, treat the input as a position value
    int n = readString.toInt();

    if(n >= 270)
    {
      Serial.print("Writing Microseconds to channel ");
      Serial.print(channel);
      Serial.print(": ");
      Serial.println(n);
      pwm.writeMicroseconds(channel, n);
    }
    else
    { 
      Serial.print("Writing Angle to channel ");
      Serial.print(channel);
      Serial.print(": ");
      Serial.println(n);
      pwm.writeMicroseconds(channel, angleToPulse(n));
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