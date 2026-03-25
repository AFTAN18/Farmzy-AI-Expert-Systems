/*
  FARMZY ESP32 Firmware
  Dependencies:
  - WiFi.h
  - WiFiClientSecure.h
  - HTTPClient.h
  - ArduinoOTA.h
  - time.h
  - OneWire.h
  - DallasTemperature.h
  - DHT.h
  - ModbusMaster.h

  Wiring (ESP32):
  - MAX485 RO -> GPIO16 (RX2)
  - MAX485 DI -> GPIO17 (TX2)
  - DS18B20 DATA -> GPIO4
  - DHT22 DATA -> GPIO5
  - pH analog -> GPIO34
  - MQ135 analog -> GPIO35
  - Soil moisture analog -> GPIO32
  - Built-in LED -> GPIO2

  ThingSpeak Field Mapping:
  F1=N, F2=P, F3=K, F4=Temp, F5=Humidity, F6=pH, F7=Gas, F8=Soil Moisture
*/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoOTA.h>
#include <time.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <DHT.h>
#include <ModbusMaster.h>

#define SIMULATION_MODE 1

#define LED_PIN 2
#define ONE_WIRE_PIN 4
#define DHT_PIN 5
#define PH_PIN 34
#define MQ135_PIN 35
#define SOIL_PIN 32

#define DHT_TYPE DHT22

const char *WIFI_SSID = "YOUR_WIFI_SSID";
const char *WIFI_PASS = "YOUR_WIFI_PASSWORD";

const char *THINGSPEAK_API_KEY = "YOUR_THINGSPEAK_WRITE_KEY";
const char *THINGSPEAK_ENDPOINT = "https://api.thingspeak.com/update";

const long GMT_OFFSET_SEC = 19800;   // UTC+5:30 IST
const int DAYLIGHT_OFFSET_SEC = 0;

unsigned long lastUploadMs = 0;
unsigned long lastDebugMs = 0;

float simN = 80, simP = 60, simK = 80;
float simPH = 6.2;
float simGas = 350;
float simMoisture = 80;
float cyclePos = 0;

enum DeviceStatus {
  STATUS_OK,
  STATUS_WIFI_ERROR,
  STATUS_SENSOR_ERROR
};

DeviceStatus currentStatus = STATUS_OK;

OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature ds18b20(&oneWire);
DHT dht(DHT_PIN, DHT_TYPE);
ModbusMaster npkNode;

struct SensorPacket {
  float nitrogen;
  float phosphorus;
  float potassium;
  float temperature;
  float humidity;
  float ph;
  float gas;
  float soil;
};

float readPHFromADC() {
  int raw = analogRead(PH_PIN);
  float voltage = (raw / 4095.0f) * 3.3f;

  // Two-point calibration example (pH4 and pH7)
  float v4 = 2.95f;
  float v7 = 2.50f;
  float slope = (7.0f - 4.0f) / (v7 - v4);
  float ph = 7.0f + slope * (voltage - v7);
  return ph;
}

float readSoilPercent() {
  int raw = analogRead(SOIL_PIN);
  // calibrated: 4095 dry, 1500 wet
  float pct = 100.0f * (4095.0f - raw) / (4095.0f - 1500.0f);
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return pct;
}

float readGasPPM() {
  int raw = analogRead(MQ135_PIN);
  float voltage = (raw / 4095.0f) * 3.3f;
  float rs = (3.3f - voltage) / max(voltage, 0.01f);
  float r0 = 0.9f;
  float ratio = rs / r0;
  float ppm = 116.6f * pow(ratio, -2.769f);
  return ppm;
}

bool readNPKModbus(float &n, float &p, float &k) {
#if SIMULATION_MODE
  n = simN;
  p = simP;
  k = simK;
  return true;
#else
  uint8_t result = npkNode.readHoldingRegisters(0x0000, 3);
  if (result != npkNode.ku8MBSuccess) {
    return false;
  }
  n = npkNode.getResponseBuffer(0);
  p = npkNode.getResponseBuffer(1);
  k = npkNode.getResponseBuffer(2);
  return true;
#endif
}

void updateSimulation(SensorPacket &pkt) {
  simN = constrain(simN + random(-2, 3), 0, 140);
  simP = constrain(simP + random(-2, 3), 0, 145);
  simK = constrain(simK + random(-3, 4), 0, 205);

  cyclePos += 1.0f;
  float t = millis() / 1000.0f;
  pkt.temperature = 31.0f + 7.0f * sin(2 * PI * t / 60.0f);
  pkt.humidity = constrain(92.0f - pkt.temperature + random(-3, 4), 20, 95);

  simPH = constrain(simPH + random(-3, 4) * 0.02f, 5.7f, 6.8f);
  simGas += random(-4, 5);
  if (random(0, 100) > 94) {
    simGas = 500 + random(-20, 20);
  }
  simGas = constrain(simGas, 300, 520);

  // moisture drops from 80 -> 20 over 30 minutes and resets
  simMoisture -= 0.033f;
  if (simMoisture < 20) {
    simMoisture = 80;
  }

  pkt.nitrogen = simN;
  pkt.phosphorus = simP;
  pkt.potassium = simK;
  pkt.ph = simPH;
  pkt.gas = simGas;
  pkt.soil = simMoisture;
}

bool readSensors(SensorPacket &pkt) {
#if SIMULATION_MODE
  updateSimulation(pkt);
  return true;
#else
  float n, p, k;
  if (!readNPKModbus(n, p, k)) {
    return false;
  }

  ds18b20.requestTemperatures();
  float temp = ds18b20.getTempCByIndex(0);
  float hum = dht.readHumidity();

  if (isnan(temp) || isnan(hum)) {
    return false;
  }

  pkt.nitrogen = n;
  pkt.phosphorus = p;
  pkt.potassium = k;
  pkt.temperature = temp;
  pkt.humidity = hum;
  pkt.ph = readPHFromADC();
  pkt.gas = readGasPPM();
  pkt.soil = readSoilPercent();
  return true;
#endif
}

void ledPattern() {
  static unsigned long previous = 0;
  static bool state = false;
  unsigned long now = millis();

  unsigned long interval = 1000;
  if (currentStatus == STATUS_WIFI_ERROR) {
    interval = 150;
  } else if (currentStatus == STATUS_SENSOR_ERROR) {
    interval = 300;
  }

  if (now - previous >= interval) {
    previous = now;
    state = !state;
    digitalWrite(LED_PIN, state ? HIGH : LOW);
  }
}

bool uploadThingSpeak(const SensorPacket &pkt) {
  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient https;
  String url = String(THINGSPEAK_ENDPOINT) +
               "?api_key=" + THINGSPEAK_API_KEY +
               "&field1=" + String(pkt.nitrogen, 2) +
               "&field2=" + String(pkt.phosphorus, 2) +
               "&field3=" + String(pkt.potassium, 2) +
               "&field4=" + String(pkt.temperature, 2) +
               "&field5=" + String(pkt.humidity, 2) +
               "&field6=" + String(pkt.ph, 2) +
               "&field7=" + String(pkt.gas, 2) +
               "&field8=" + String(pkt.soil, 2);

  if (!https.begin(client, url)) {
    return false;
  }

  int code = https.GET();
  https.end();
  return code > 0;
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(400);
  }

  currentStatus = (WiFi.status() == WL_CONNECTED) ? STATUS_OK : STATUS_WIFI_ERROR;
}

void syncNTP() {
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, "pool.ntp.org", "time.nist.gov");
  struct tm info;
  if (!getLocalTime(&info)) {
    Serial.println("NTP sync failed");
  }
}

void setupOTA() {
  ArduinoOTA.setHostname("farmzy-esp32");
  ArduinoOTA.begin();
}

void printDebug(const SensorPacket &pkt) {
  Serial.println("---------------------------------");
  Serial.printf("N: %.2f mg/kg\n", pkt.nitrogen);
  Serial.printf("P: %.2f mg/kg\n", pkt.phosphorus);
  Serial.printf("K: %.2f mg/kg\n", pkt.potassium);
  Serial.printf("Temp: %.2f C\n", pkt.temperature);
  Serial.printf("Humidity: %.2f %%\n", pkt.humidity);
  Serial.printf("pH: %.2f\n", pkt.ph);
  Serial.printf("Gas: %.2f ppm\n", pkt.gas);
  Serial.printf("Soil Moisture: %.2f %%\n", pkt.soil);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  analogReadResolution(12);

  dht.begin();
  ds18b20.begin();

  Serial2.begin(9600, SERIAL_8N1, 16, 17);
  npkNode.begin(1, Serial2);

  connectWiFi();
  syncNTP();
  setupOTA();
}

void loop() {
  ArduinoOTA.handle();
  ledPattern();

  if (WiFi.status() != WL_CONNECTED) {
    currentStatus = STATUS_WIFI_ERROR;
    connectWiFi();
    return;
  }

  SensorPacket pkt;
  bool ok = readSensors(pkt);
  if (!ok) {
    currentStatus = STATUS_SENSOR_ERROR;
    delay(1000);
    return;
  }
  currentStatus = STATUS_OK;

  unsigned long now = millis();

  if (now - lastDebugMs >= 10000) {
    lastDebugMs = now;
    printDebug(pkt);
  }

  if (now - lastUploadMs >= 60000) {
    lastUploadMs = now;
    bool uploaded = uploadThingSpeak(pkt);
    Serial.println(uploaded ? "ThingSpeak upload: OK" : "ThingSpeak upload: FAILED");
  }
}
