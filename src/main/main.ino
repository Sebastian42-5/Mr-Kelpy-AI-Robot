#include <Wire.h>
#include <Servo.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_Sensor.h>
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

  // digitalWrite(in1, HIGH);
  // digitalWrite(in2, LOW);
  // digitalWrite(in3, HIGH);
  // digitalWrite(in4, LOW);
  // analogWrite(ena, 120);
  // analogWrite(enb, 120);
  // delay(2000);

  // digitalWrite(in1, LOW);
  // digitalWrite(in2, LOW);
  // digitalWrite(in3, LOW);
  // digitalWrite(in4, LOW);
  // delay(2000);

  // digitalWrite(in1, LOW);
  // digitalWrite(in2, HIGH);
  // digitalWrite(in3, LOW);
  // digitalWrite(in4, HIGH);
  // analogWrite(ena, 120);
  // analogWrite(enb, 120);
  // delay(2000);

  // digitalWrite(in1, LOW);
  // digitalWrite(in2, LOW);
  // digitalWrite(in3, LOW);
  // digitalWrite(in4, LOW);
  // delay(2000);

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)){
    Serial.println(F("Serial allocation failed"));
    for(;;);
  }

  if(display.begin(SSD1306_SWITCHCAPVCC, 0x3C)){
    Serial.println("screen initialized");
  }

  roboEyes.begin(&display, SCREEN_WIDTH, SCREEN_HEIGHT, 120);
  roboEyes.open();
  roboEyes.setAutoblinker(ON, 3, 2);
  roboEyes.setIdleMode(ON, 2, 2);
  roboEyes.setWidth(80, 36);
  roboEyes.setHeight(28, 18);
  roboEyes.setBorderradius(4, 8); 
  roboEyes.setSpacebetween(1); 
  roboEyes.setCyclops(ON);
  roboEyes.setMood(DEFAULT);

}

void loop() {
  // put your main code here, to run repeatedly:
  // if(Serial.available()){
  //   String data = Serial.readStringUntil("\n");
  // }
  roboEyes.update();
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