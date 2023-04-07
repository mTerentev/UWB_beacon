#include <ESP8266WiFi.h>
#include <espnow.h>

uint8_t broadcastAddress[] = { 0x2C, 0x3A, 0xE8, 0x42, 0xA3, 0xB6 };

bool transmitting = true;

String success;

typedef struct struct_message {
  String msg;
} struct_message;

// Create a struct_message called DHTReadings to hold sensor readings
struct_message Message;

// Callback when data is sent
void OnDataSent(uint8_t *mac_addr, uint8_t sendStatus) {
}

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);
  if (esp_now_init() != 0) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  esp_now_set_self_role(ESP_NOW_ROLE_COMBO);
  esp_now_register_send_cb(OnDataSent);
  esp_now_add_peer(broadcastAddress, ESP_NOW_ROLE_COMBO, 1, NULL, 0);

  pinMode(0, INPUT_PULLUP);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  delay(2000);
  Serial.println("AT+switchdis=1");
}

void loop() {
  if (digitalRead(0) == LOW) {
    delay(10);
    if (digitalRead(0) == LOW) {
      transmitting = !transmitting;
      digitalWrite(LED_BUILTIN, transmitting);
      Serial.println("AT+switchdis=" + (String)transmitting);
    }
  }
  while (digitalRead(0) == LOW);
  //Serial.println("AT");
  unsigned long currentMillis = millis();
  if (Serial.available()) {

    String str = Serial.readStringUntil('\n');

    Message.msg = str.substring(2);

    // Send message via ESP-NOW
    esp_now_send(broadcastAddress, (uint8_t *)&Message, sizeof(Message));
  }
}
