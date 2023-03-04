#include "auth.h"
#include <WiFi.h> //Wifi library
#include "esp_wpa2.h" //wpa2 library for connections to Enterprise networks
#include <M5StickCPlus.h>
#include <ArduinoMqttClient.h>
const char broker[] = "info8000.ga";
int        port     = 1883;
WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);
const char topic_status[] = "ugaelee2045sp23/kjohnsen/light_status";
const char topic_control_color[] = "ugaelee2045sp23/kjohnsen/light_control_color";
const char topic_control_status[] = "ugaelee2045sp23/kjohnsen/light_control_status";
char buffer[100];
int r;
int g;
int b;
int status;

//stolen from https://forums.adafruit.com/viewtopic.php?t=21536
uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b)
{
  return ((r / 8) << 11) | ((g / 4) << 5) | (b / 8);
}

void updateStatus(){
  M5.Axp.ScreenBreath(status?15:0);
  //colors are in 565 format
  M5.Lcd.fillScreen(rgb565(r,g,b));
}

void onMqttMessage(int messageSize) {
  if(mqttClient.messageTopic() == topic_control_color){
    //read 3 unsigned bytes
    r = mqttClient.read();
    g = mqttClient.read();
    b = mqttClient.read();
    Serial.println(r);
    Serial.println(g);
    Serial.println(b);
  }
  if(mqttClient.messageTopic() == topic_control_status){
    status = mqttClient.read();
    Serial.println(status);
  }
  updateStatus();
  sendStatus();
}
unsigned long last_time;
void setup() {
  M5.begin();
  M5.Lcd.fillScreen(BLACK);
  WiFi.disconnect(true);  //disconnect form wifi to set new wifi connection
  WiFi.mode(WIFI_STA); //init wifi mode
  #ifdef USE_EAP
    esp_wifi_sta_wpa2_ent_set_identity((uint8_t *)EAP_ANONYMOUS_IDENTITY, strlen(EAP_ANONYMOUS_IDENTITY));
    esp_wifi_sta_wpa2_ent_set_username((uint8_t *)EAP_IDENTITY, strlen(EAP_IDENTITY));
    esp_wifi_sta_wpa2_ent_set_password((uint8_t *)EAP_PASSWORD, strlen(EAP_PASSWORD));
    esp_wifi_sta_wpa2_ent_enable();
    WiFi.begin(ssid); //connect to wifi
  #else
    WiFi.begin(ssid,WPA_PASSWORD);
  #endif
  WiFi.setSleep(false);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Waiting for connection");
  }
  IPAddress ip = WiFi.localIP();
  Serial.println(ip);
  M5.Lcd.print(ip);
  
  //added after connected in setup
  mqttClient.onMessage(onMqttMessage);
  mqttClient.setUsernamePassword("giiuser","giipassword");
  mqttClient.connect(broker, port);
  mqttClient.subscribe(topic_control_color);
  mqttClient.subscribe(topic_control_status);
  last_time = millis();
  updateStatus();
}
void sendStatus(){
  mqttClient.beginMessage(topic_status);
  mqttClient.write(status);
  mqttClient.write(r);
  mqttClient.write(g);
  mqttClient.write(b);
  mqttClient.endMessage();
}
int waitingForRelease = 0;
void loop(){
  mqttClient.poll();
  if(millis()-last_time > 2000){
    sendStatus();
    last_time = millis();
  }

  if(digitalRead(37)==LOW && !waitingForRelease){
    status = !status;
    updateStatus();
    sendStatus();
    waitingForRelease = 1;
  }
  if(digitalRead(37)==HIGH){
    waitingForRelease = 0;
  }
}