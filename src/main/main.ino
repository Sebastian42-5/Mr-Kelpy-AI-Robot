#include <Wire.h>
#include <Servo.h>
#include <Adafruit_SSD1306.h>
#include <splash.h>
#include <HCSR04.h>
#include <FluxGarage_RoboEyes.h>



int clawPin = 3;
int tailPin = 4;
int ena = 5; 
int in1 = 6;
int in2 = 7;
int in3 = 8;
int in4 = 9;
int enb = 10;
int echoPin = 11;
int trigPin = 12;
int touchSensor = 13; 

Servo tail;
Servo claw; 

long duration;
int distance;

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1


Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
RoboEyes<Adafruit_SSD1306> roboEyes(display);

void setup() {

  Serial.begin(9600);

  Serial.println("hello");

  claw.attach(clawPin);
  tail.attach(tailPin);

  pinMode(ena, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(touchSensor, INPUT_PULLUP);

  
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)){
    Serial.println(F("Serial allocation failed"));
    for(;;);
  }

  if(display.begin(SSD1306_SWITCHCAPVCC, 0x3C)){
    Serial.println("screen initialized");
  }

  roboEyes.begin(SCREEN_WIDTH, SCREEN_HEIGHT, 60);
  roboEyes.open();
  // roboEyes.setAutoblinker(ON, 3, 2);
  roboEyes.setIdleMode(ON, 2, 2);
  roboEyes.setWidth(80, 36);
  roboEyes.setHeight(28, 18);
  roboEyes.setBorderradius(4, 8); 
  roboEyes.setSpacebetween(1); 
  roboEyes.setCyclops(ON);
  roboEyes.setMood(DEFAULT);

}

void moveForward() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  analogWrite(ena, 0);
  analogWrite(enb, 0);
  delay(1000);

  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  analogWrite(ena, 150);
  analogWrite(enb, 150);
  delay(1000);

  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  delay(1000);
}

void moveBackward() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  analogWrite(ena, 0);
  analogWrite(enb, 0);
  delay(1000);

  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  analogWrite(ena, 100);
  analogWrite(enb, 100);
  delay(1000);

  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  delay(2000);
}

void turnRight() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  analogWrite(ena, 0);
  analogWrite(enb, 0);
  delay(1000);

  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  analogWrite(ena, 100);
  analogWrite(enb, 100);
  delay(1000);

  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  delay(2000);
}

void turnLeft() {
   digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  analogWrite(ena, 0);
  analogWrite(enb, 0);
  delay(1000);

  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  analogWrite(ena, 100);
  analogWrite(enb, 100);
  delay(1000);

  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  delay(2000);
}

void loop() {
  if(Serial.available()){
    String data = Serial.readStringUntil("\n");
    Serial.println("recieved.");

    if(data == "move forward"){
      moveForward();
      delay(500);
    } else if(data == "move backward"){
      moveBackward();
      delay(500);
    }

  }
  roboEyes.update();
  roboEyes.setMood(0);
  int touchDetected = digitalRead(touchSensor);
  // Serial.println(touchDetected);

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10); 
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2;
  if(touchDetected == LOW){
    Serial.println("happy mode");
    roboEyes.setMood(HAPPY);
    for(int pos = 0; pos < 30; pos += 3){
      tail.write(pos);
      delay(20);
    }
    for(int pos = 30; pos > 0; pos -= 3){
      tail.write(pos);
      delay(20);
    }
} 


}
