#include <FastLED.h>

// Configuration servo
const int servoPin = 9;
int pulseWidth = 500;            // 🔹 Démarrage à 0°
const int minPulse = 500;
const int maxPulse = 2500;
const int step = 10;             // µs par étape
int direction = 1;               // 🔼 Incrémente vers 180°

// Configuration LED WS2812
#define LED_PIN 6
#define NUM_LEDS 1
CRGB leds[NUM_LEDS];

// Configuration communication série
volatile bool newRGBReceived = false;
volatile uint8_t rgbBuffer[3] = {255, 0, 0}; // Rouge par défaut
volatile bool rgbComponentsReceived[3] = {false, false, false}; // R, G, B reçus

// Timing
unsigned long lastServoUpdate = 0;
unsigned long startTime = 0;
const unsigned long stepInterval = 5000;   // 5 sec par step pour servo
const unsigned long pauseDuration = 10000; // 10 sec de pause après démarrage

enum State {
  INIT_MOVE,
  WAIT_AT_BOTTOM,
  OSCILLATE
};

State state = INIT_MOVE;

void setup() {
  // Configuration série
  Serial.begin(9600);
  
  // Configuration servo
  pinMode(servoPin, OUTPUT);
  digitalWrite(servoPin, LOW);

  // Configuration LED WS2812
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(100);
  
  // Couleur initiale (rouge)
  leds[0] = CRGB(rgbBuffer[0], rgbBuffer[1], rgbBuffer[2]);
  FastLED.show();

  // Envoi initial pour forcer position 0°
  sendServoPulse(pulseWidth);
  startTime = millis();
  state = WAIT_AT_BOTTOM;
  
  Serial.println("Arduino servo + LED ready");
}

void loop() {
  unsigned long now = millis();

  // Gestion de la réception série pour les couleurs RGB
  processSerialInput();

  // Gestion du servo
  updateServo(now);
  
  // Mise à jour LED si nouvelles données RGB reçues
  updateLED();
}

void updateServo(unsigned long now) {
  switch (state) {
    case WAIT_AT_BOTTOM:
      if (now - startTime >= pauseDuration) {
        lastServoUpdate = now;
        state = OSCILLATE;
      }
      break;

    case OSCILLATE:
      if (now - lastServoUpdate >= stepInterval) {
        lastServoUpdate = now;

        // Mise à jour de la largeur d'impulsion
        pulseWidth += direction * step;

        // Rebond aux extrémités
        if (pulseWidth >= maxPulse || pulseWidth <= minPulse) {
          direction *= -1;
          pulseWidth = constrain(pulseWidth, minPulse, maxPulse);
        }

        sendServoPulse(pulseWidth);
      }
      break;

    default:
      break;
  }
}

void updateLED() {
  if (newRGBReceived) {
    // Application directe et immédiate des nouvelles valeurs RGB
    noInterrupts();
    leds[0] = CRGB(rgbBuffer[0], rgbBuffer[1], rgbBuffer[2]);
    newRGBReceived = false;
    interrupts();
    
    FastLED.show();
    
    Serial.print("LED updated: ");
    Serial.print(rgbBuffer[0]); Serial.print(",");
    Serial.print(rgbBuffer[1]); Serial.print(",");
    Serial.println(rgbBuffer[2]);
  }
}

// Envoie une impulsion PWM unique (~20 ms période servo)
void sendServoPulse(int us) {
  digitalWrite(servoPin, HIGH);
  delayMicroseconds(us);
  digitalWrite(servoPin, LOW);
  delay(20);
}

// Gestion de la réception série pour couleurs RGB
void processSerialInput() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    // Format attendu: "rgb,255,128,64" (complet en une fois)
    if (input.startsWith("rgb,")) {
      // Format CSV: rgb,r,g,b
      int firstComma = input.indexOf(',', 4);
      int secondComma = input.indexOf(',', firstComma + 1);
      
      if (firstComma > 0 && secondComma > 0) {
        int r = input.substring(4, firstComma).toInt();
        int g = input.substring(firstComma + 1, secondComma).toInt();
        int b = input.substring(secondComma + 1).toInt();
        
        updateRGBBuffer(r, g, b);
        Serial.print("RGB updated: ");
        Serial.print(r); Serial.print(",");
        Serial.print(g); Serial.print(",");
        Serial.println(b);
      }
    }
    // Format compact: r255g128b64 (complet en une fois)
    else if (input.startsWith("r") && input.indexOf("g") > 0 && input.indexOf("b") > 0) {
      int gPos = input.indexOf('g');
      int bPos = input.indexOf('b');
      
      if (gPos > 1 && bPos > gPos) {
        int r = input.substring(1, gPos).toInt();
        int g = input.substring(gPos + 1, bPos).toInt();
        int b = input.substring(bPos + 1).toInt();
        
        updateRGBBuffer(r, g, b);
        Serial.print("RGB updated: ");
        Serial.print(r); Serial.print(",");
        Serial.print(g); Serial.print(",");
        Serial.println(b);
      }
    }
    // Format composantes individuelles: "r255", "g128", "b64"
    else if (input.startsWith("r") && input.length() > 1) {
      int r = input.substring(1).toInt();
      updateRGBComponent(0, r); // Index 0 = Rouge
    }
    else if (input.startsWith("g") && input.length() > 1) {
      int g = input.substring(1).toInt();
      updateRGBComponent(1, g); // Index 1 = Vert
    }
    else if (input.startsWith("b") && input.length() > 1) {
      int b = input.substring(1).toInt();
      updateRGBComponent(2, b); // Index 2 = Bleu
    }
  }
}

// Met à jour une composante RGB et vérifie si le triplet est complet
void updateRGBComponent(uint8_t component, uint8_t value) {
  noInterrupts();
  rgbBuffer[component] = constrain(value, 0, 255);
  rgbComponentsReceived[component] = true;
  
  // Vérifier si toutes les composantes sont reçues
  if (rgbComponentsReceived[0] && rgbComponentsReceived[1] && rgbComponentsReceived[2]) {
    newRGBReceived = true;
    // Reset des flags
    rgbComponentsReceived[0] = false;
    rgbComponentsReceived[1] = false;
    rgbComponentsReceived[2] = false;
  }
  interrupts();
}

// Met à jour le buffer RGB de manière atomique
void updateRGBBuffer(uint8_t r, uint8_t g, uint8_t b) {
  noInterrupts();
  rgbBuffer[0] = constrain(r, 0, 255);
  rgbBuffer[1] = constrain(g, 0, 255);
  rgbBuffer[2] = constrain(b, 0, 255);
  newRGBReceived = true;
  interrupts();
}