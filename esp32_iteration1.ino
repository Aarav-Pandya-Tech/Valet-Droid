#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "Aarav1";             // Your Wi-Fi SSID
const char* password = "117@pranav";     // Your Wi-Fi password

const char* serverIP = "http://valetdroid.local";  // Flask server address

String inputString = "";   // Stores input from Serial Monitor

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.println("Type 'get' or send a JSON to POST:");
}

void loop() {
  if (Serial.available()) {
    inputString = Serial.readStringUntil('\n');  // Read until newline
    inputString.trim();  // Remove extra spaces and line breaks

    if (inputString == "get") {
      getDataFromServer();
    } else if (inputString.startsWith("{") && inputString.endsWith("}")) {
      postDataToServer(inputString);
    } else {
      Serial.println("Invalid input. Type 'get' or send a valid JSON.");
    }
  }
}

void getDataFromServer() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(serverIP) + "/data");

    int httpCode = http.GET();

    if (httpCode > 0) {
      String payload = http.getString();
      Serial.println("GET response:");
      Serial.println(payload);
    } else {
      Serial.println("GET request failed");
    }

    http.end();
  }
}

void postDataToServer(String jsonStr) {
  if (WiFi.status() == WL_CONNECTED) {
    // Check if JSON is valid
    StaticJsonDocument<200> jsonDoc;
    DeserializationError error = deserializeJson(jsonDoc, jsonStr);

    if (error) {
      Serial.println("Invalid JSON format");
      return;
    }

    HTTPClient http;
    http.begin(String(serverIP) + "/update");
    http.addHeader("Content-Type", "application/json");

    int httpCode = http.POST(jsonStr);

    if (httpCode > 0) {
      String response = http.getString();
      Serial.println("POST response:");
      Serial.println(response);
    } else {
      Serial.print("POST failed, code: ");
      Serial.println(httpCode);
    }

    http.end();
  }
}
