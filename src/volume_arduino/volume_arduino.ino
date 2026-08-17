

int pot;
int potPin = A0;

void setup() {
  // put your setup code here, to run once:

  Serial.begin(9600);

}

void loop() {
  // put your main code here, to run repeatedly:
  pot = analogRead(potPin);
  Serial.println(pot);
  delay(100);
}
