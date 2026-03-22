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
int echo = 11;
int trig = 12;
int touchSensor = 13; 

Servo tail;
Servo claw; 

roboEyes roboEyes;

long duration;
int distance;

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void setup() {
  // put your setup code here, to run once:

  Serial.begin(9600);

  claw.attach(claw);
  tail.attach(tail);

  pinMode(ena, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);
  pinMode(touchSensor, INPUT);

  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  analogWrite(ena, 120);
  analogWrite(enb, 120);
  delay(2000);

  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  delay(2000);

  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  analogWrite(ena, 120);
  analogWrite(enb, 120);
  delay(2000);

  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  delay(2000);

  roboEyes.begin(SCREEN_WIDTH, SCREEN_HEIGHT, 100);
  roboEyes.setAutoblinker(ON, 3, 2);
  roboEyes.setIdleMode(ON, 2, 2);
  roboEyes.setWidth(80, 36);
  roboEyes.setHeight(28, 18);
  roboEyes.setBorderradius(4, 8); 
  roboEyes.setSpacebetween(1); 
  roboEyes.setCyclops(ON);

}

void loop() {
  // put your main code here, to run repeatedly:
  // if(Serial.available()){
  //   String data = Serial.readStringUntil("\n");
  // }
  roboEyes.setMood(DEFAULT);
  touchDetected = digitalRead(tocuhSensor);

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10); 
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2;
  if(touchDetected){
    roboEyes.setMood(HAPPY);
    for(int pos = 0; pos < 30; pos += 1){
      tail.write(pos);
      delay(100);
    }
    for(int pos = 30; pos > 0; pos -= 1){
      tail.write(pos);
      delay(100);
    }
  }


}