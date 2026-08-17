#include <Wire.h>

const int MPU = 0x68;

int16_t raw_ax, raw_ay, raw_az;
int16_t raw_gx, raw_gy, raw_gz;
int16_t temp;

float ax, ay, az;
float gx, gy, gz;

float gx_offset = 0;
float gy_offset = 0;

float roll_acc, pitch_acc;
float roll = 0;
float pitch = 0;

unsigned long prev_time;
float dt;


void setup() {
  // put your setup code here, to run once:
  Wire.begin();
  Serial.begin(9600);
  while(!Serial);

  Wire.beginTransmission(MPU);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  Serial.println("Calibrating gyro... Keep IMU flat and still.");
  long sum_gx = 0, sum_gy = 0;
  const int samples = 500;
  for (int i = 0; i < samples; i++) {
    readRawData();
    sum_gx += raw_gx;
    sum_gy += raw_gy;
    delay(3);
  }
  gx_offset = (float)sum_gx / samples;
  gy_offset = (float)sum_gy / samples;
  Serial.println("Calibration complete.");

  prev_time = millis();
}

void loop() {
  // put your main code here, to run repeatedly:
  readRawData();

  // 1. Convert Accelerometer Raw LSB to 'g' units
  ax = raw_ax / 16384.0;
  ay = raw_ay / 16384.0;
  az = raw_az / 16384.0;

  // 2. Convert Gyroscope Raw LSB to degrees per second (°/s) and subtract offset
  gx = (raw_gx - gx_offset) / 131.0;
  gy = (raw_gy - gy_offset) / 131.0;

  // Calculate elapsed time (dt) in seconds
  unsigned long current_time = millis();
  dt = (current_time - prev_time) / 1000.0;
  prev_time = current_time;

  // 3. Compute absolute angles from Accelerometer using Trigonometry
  // atan2 returns radians; multiply by 180/PI to get degrees
  roll_acc  = atan2(ay, az) * 180.0 / M_PI;
  pitch_acc = atan2(-ax, sqrt(ay * ay + az * az)) * 180.0 / M_PI;

  // 4. Complementary Filter Fusion
  // High weighting (0.98) on smooth gyro integration; low weighting (0.02) on stable accel absolute reference
  roll  = 0.98 * (roll + gx * dt) + 0.02 * roll_acc;
  pitch = 0.98 * (pitch + gy * dt) + 0.02 * pitch_acc;

  // Print filtered angles
  Serial.print("Roll: "); Serial.print(roll);
  Serial.print(" | Pitch: "); Serial.println(pitch);

  delay(10); 
}

void readRawData() {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);
  Wire.endTransmission(false);

  Wire.requestFrom(MPU, 14, true);

  // Read accelerometer data
  raw_ax = Wire.read() << 8 | Wire.read(); // 0x3B (ACCEL_XOUT_H) & 0x3C (ACCEL_XOUT_L)
  raw_ay = Wire.read() << 8 | Wire.read(); // 0x3D (ACCEL_YOUT_H) & 0x3E (ACCEL_YOUT_L)
  raw_az = Wire.read() << 8 | Wire.read(); // 0x3F (ACCEL_ZOUT_H) & 0x40 (ACCEL_ZOUT_L)

  // Read temperature data
  temp = Wire.read() << 8 | Wire.read(); // 0x41 (TEMP_OUT_H) & 0x42 (TEMP_OUT_L)

  // Read gyroscope data
  raw_gx = Wire.read() << 8 | Wire.read(); // 0x43 (GYRO_XOUT_H) & 0x44 (GYRO_XOUT_L)
  raw_gy = Wire.read() << 8 | Wire.read(); // 0x45 (GYRO_YOUT_H) & 0x46 (GYRO_YOUT_L)
  raw_gz = Wire.read() << 8 | Wire.read(); // 0x47 (GYRO_ZOUT_H) & 0x48 (GYRO_ZOUT_L)

  // Output data to serial monitor and plotter
  // For Serial Plotter, it's important that all values are on one line, separated by tabs.
  // This will allow the plotter to display each parameter as a separate line.
  
  delay(100);
}
