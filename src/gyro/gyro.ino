#include <Wire.h>

const int MPU = 0x68;

int16_t raw_ax, raw_ay, raw_az;
int16_t raw_gx, raw_gy, raw_gz;
int16_t temp;

float gx_offset = 0, gy_offset = 0, gz_offset = 0;

float target_yaw = 0;  // the reference point for the yaw will always be zero 
float TURNING_TOLERANCE = 2.0; // how much the robot can deviate from the target angle before it stops turning
float error = 0; // the difference between the target angle and the current angle

enum RobotState {
  IDLE,
  TURNING,
  MOVING_FORWARD,
  MOVING_BACKWARD
};

RobotState robot_state = IDLE;

unsigned long prev_time;
float dt;

unsigned long last_report_time = 0;
const unsigned long REPORT_INTERVAL = 100; // the current yaw of the robot gets reported every 100 milliseconds

int ena = 5, in1 = 6, in2 = 7, in3 = 8, in4 = 9, enb = 10;


bool turningDone = false;

int echoPin = 12;
int trigPin = 11;

void setup() {
  pinMode(ena, OUTPUT); pinMode(in1, OUTPUT); pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT); pinMode(in4, OUTPUT); pinMode(enb, OUTPUT);

  pinMode(trigPin, OUTPUT); pinMode(echoPin, INPUT);



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

  handleTurningCommand();

  float gz = (raw_gz - gz_offset) / 131.0; // deg/s

  unsigned long current_time = millis();
  dt = (current_time - prev_time) / 1000.0;
  prev_time = current_time;

  target_yaw += gz * dt;

  // ultrasonic logic

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);      

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);     
  digitalWrite(trigPin, LOW);

  float duration = pulseIn(echoPin, HIGH); 
 
  float distanceCm = (duration * 0.0343) / 2; 

  Serial.print("DISTANCE: ");
  Serial.print(distanceCm);
  Serial.println(" cm");

  delay(500); 

  if (robot_state == TURNING) {
    float error = target_yaw - desired_angle_change;

    while (error > 180) error -= 360; // Normalize to [-180, 180]
    while (error < -180) error += 360; // Normalize to [-180, 180]

    if (abs(error) <= TURNING_TOLERANCE) {
      stop_motor();
      robot_state = IDLE;
      Serial.println("DONE");
    } else {
        if(error > 0) {
          turnLeft();
        } else {
          turnRight();
        } 
        if (current_time - last_report_time >= REPORT_INTERVAL) {
          Serial.print("YAW: "); Serial.println(target_yaw);
          last_report_time = current_time;
        }
    }

    elif (current_time - last_report_time >= REPORT_INTERVAL) {
    Serial.print("YAW: "); Serial.println(target_yaw);
    last_report_time = current_time;
    }

    elif (robot_state == MOVING_FORWARD) {
      goForward();
    } else if (robot_state == MOVING_BACKWARD) {
      goBackward();
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

void handleTurningCommand() {

  if(Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.startsWith("TURN") && robot_state == IDLE) {

      float desired_angle_change = command.substring(5).toFloat(); // Extract the desired angle change from the command

      target_yaw = yaw + desired_angle_change; // Set the target yaw based on the current yaw and the desired change
      
      while(target_yaw > 180) target_yaw -= 360; // Normalize to [-180, 180]
      while(target_yaw < -180) target_yaw += 360; // Normalize to [-180, 180]

      robot_state = TURNING;

      Serial.println("TARGET: " + String(target_yaw));
    }
  }
}
