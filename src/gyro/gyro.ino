#include <Wire.h>

const int MPU = 0x68;

int16_t raw_ax, raw_ay, raw_az;
int16_t raw_gx, raw_gy, raw_gz;
int16_t temp;

float gx_offset = 0, gy_offset = 0, gz_offset = 0;

float yaw = 0;  // the reference point for the yaw will always be zero 

unsigned long prev_time;
float dt;

int ena = 5, in1 = 6, in2 = 7, in3 = 8, in4 = 9, enb = 10;

float desired_angle_change = 90.0; // degrees
bool turningDone = false;

void setup() {
  pinMode(ena, OUTPUT); pinMode(in1, OUTPUT); pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT); pinMode(in4, OUTPUT); pinMode(enb, OUTPUT);

  Wire.begin();
  Serial.begin(9600);
  while (!Serial);

  Wire.beginTransmission(MPU);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  Serial.println("Calibrating gyro... keep robot still.");
  long sum_gx = 0, sum_gy = 0, sum_gz = 0;
  const int samples = 500;
  for (int i = 0; i < samples; i++) {
    readRawData();
    sum_gx += raw_gx;
    sum_gy += raw_gy;
    sum_gz += raw_gz;
    delay(3);
  }
  gx_offset = (float)sum_gx / samples;
  gy_offset = (float)sum_gy / samples;
  gz_offset = (float)sum_gz / samples;
  Serial.println("Calibration complete.");

  prev_time = millis();
}

void loop() {
  readRawData();

  if(Serial.available() > 0) {
    String desired_object_angle_message = Serial.readStringUntil("\n"); 
    desired_object_angle_message.trim();

    desired_angle_change = desired_object_angle_message.toInt();
  }

  float gz = (raw_gz - gz_offset) / 131.0; // deg/s

  unsigned long current_time = millis();
  dt = (current_time - prev_time) / 1000.0;
  prev_time = current_time;

  yaw += gz * dt;

  Serial.print("Yaw: "); Serial.println(yaw);

  if (!turningDone) {
    if (abs(yaw) >= desired_angle_change) {
      stop_motor();
      turningDone = true;
      Serial.println("Turn complete.");
    } else {
      turnRight();
    }
  }
}

void turnRight() {
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  analogWrite(ena, 100);
  analogWrite(enb, 100);
}

void turnLeft() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  analogWrite(ena, 100);
  analogWrite(enb, 100);
}

void goForward() {
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  analogWrite(ena, 120);
  analogWrite(enb, 120);
}

void goBackward() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  analogWrite(ena, 120);
  analogWrite(enb, 120);
}

void stop_motor() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
}

void readRawData() {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU, 14, true);

  raw_ax = Wire.read() << 8 | Wire.read();
  raw_ay = Wire.read() << 8 | Wire.read();
  raw_az = Wire.read() << 8 | Wire.read();
  temp   = Wire.read() << 8 | Wire.read();
  raw_gx = Wire.read() << 8 | Wire.read();
  raw_gy = Wire.read() << 8 | Wire.read();
  raw_gz = Wire.read() << 8 | Wire.read();
}
