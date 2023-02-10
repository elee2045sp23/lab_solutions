#include <M5StickCPlus.h>
int BTNA = 37;
long minDelay = 2000;
long maxDelay = 6000;
void setup() {
  M5.begin();
  Serial.flush();
  M5.Axp.ScreenBreath(15);
  RTC_TimeTypeDef TimeStruct;
  M5.Rtc.GetTime(&TimeStruct);
  randomSeed(TimeStruct.Seconds);  //pseudorandom
}
void waitForButton(int button, int state) {
  while (digitalRead(button) != state) {}
}
void waitForPressAndRelease(int button, int bounceTime) {
  waitForButton(button,LOW); delay(bounceTime); waitForButton(button,HIGH);
}
void printMessageLcd(char * message){
    M5.Lcd.fillScreen(BLACK); M5.Lcd.setCursor(0, 0);
    M5.Lcd.print(message);
}
void loop() {
  printMessageLcd("Hit M5 to start.\nHear the Beep.\nHit M5 again.");
  waitForPressAndRelease(BTNA, 10);
  printMessageLcd("Wait for it!");
  long beepTime = random(minDelay, maxDelay);
  long startTime = millis();
  long elapsedTime = 0;
  bool beeped = false;
  while (digitalRead(BTNA) == HIGH) {
    long currentTime = millis();
    elapsedTime = currentTime - startTime;
    if (!beeped) {
      if (elapsedTime > beepTime) {
        printMessageLcd("now!");
        M5.Beep.tone(440);
        beeped = true;
      }
    }
  }
  M5.Beep.mute();

  if (elapsedTime < beepTime) {
    printMessageLcd("Too fast!");
  } else {
    printMessageLcd("Great job!");
  }
  char buffer[100];
  sprintf(buffer,"%d,%d",beepTime,elapsedTime);
  Serial.println(buffer);
  waitForButton(BTNA, HIGH);
  delay(2000);
}