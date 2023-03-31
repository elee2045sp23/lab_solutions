
#include <M5StickCPlus.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

BLEServer* pServer = NULL; 
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;
bool advertising = false;

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "5e8be540-13b8-49bf-af35-63b725c5c066"

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer, esp_ble_gatts_cb_param_t *param) {
      Serial.println("Device connected");
      // this code isnt necessary, but it makes the bluetooth go faster
      pServer->updateConnParams(param->connect.remote_bda, 0x06, 0x06, 0, 100);
      deviceConnected = true;
      advertising = false;
    };

    void onDisconnect(BLEServer* pServer) {
      Serial.println("Device disconnected");
      deviceConnected = false;
    }
};

void setup() {
  M5.begin();
  M5.IMU.Init();

  // Create the BLE Device
  BLEDevice::init("M5StickCPlus-Kyle");

  // Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create a BLE Characteristic
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ   |
                      BLECharacteristic::PROPERTY_NOTIFY 
                    );

  // Create a BLE Descriptor that clients may try to write to suggest they actually want notifications
  pCharacteristic->addDescriptor(new BLE2902());

  // Start the service
  pService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x06);  
  pAdvertising->setMaxPreferred(0x0C);
  BLEDevice::startAdvertising();
  Serial.println("Waiting a client connection to notify...");
}
#pragma pack(1) //force tight packing
typedef struct {
  float accx,accy,accz;
  uint8_t buttonA;
  uint16_t batt;
} Packet;
void loop() {
    // notify changed value
    if (deviceConnected) {
        Packet p;
        M5.IMU.getAccelData(&p.accx, &p.accy, &p.accz);
        p.batt = M5.Axp.GetVbatData();
        p.buttonA = 1-digitalRead(37); // front button, converted to 1 pressed, 0 released
        pCharacteristic->setValue((uint8_t*)&p, sizeof(Packet));
        pCharacteristic->notify();
        delay(1); // bluetooth stack will go into congestion, if too many packets are sent
    }
    // disconnecting
    if (!deviceConnected && !advertising) {
        delay(500); // give the bluetooth stack the chance to get things ready
        pServer->startAdvertising(); // restart advertising
        Serial.println("start advertising");
        advertising = true;
    }
    
}