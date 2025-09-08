/*
  Tourne Disque Synesthésique - Contrôleur Servo + LED (mode temporel)

  Fonctionnalités:
  - Oscillation d'un servo entre minPulse et maxPulse.
  - Avancement automatique d'un step toutes les 30 secondes.
  - LED WS2812 (1 pixel) avec séquence rainbow d'accueil de 5 secondes.
  - Mise à jour LED via commandes série simples.

  Commandes série (terminer par \n ou \r):
    rgb,R,G,B        -> définit couleur immédiatement (ex: rgb,120,40,255)
    r123g045b255     -> format compact ordre strict
    r200 / g10 / b90 -> composantes unitaires; appliquées quand les 3 reçues
*/
#include <Arduino.h>
#include <FastLED.h>
#include <Servo.h>

// Configuration servo (Servo lib pour timing stable)
const int servoPin = 9;
int pulseWidth = 500;            // µs (position actuelle)
const int minPulse = 500;
const int maxPulse = 2350;
int direction = 1;
Servo canvasServo;
int lastWrittenPulse = -1;       // pour n'écrire que si changement

// Configuration LED WS2812
#define LED_PIN 6
#define NUM_LEDS 1
CRGB leds[NUM_LEDS];

// Variables pour séquence d'accueil rainbow
bool rainbowSequence = true;
unsigned long rainbowStart = 0;
const unsigned long rainbowDuration = 5000; // 5 secondes

// Configuration communication série
bool newRGBReceived = false;
uint8_t rgbBuffer[3] = {0, 0, 255}; // Bleu par défaut
bool rgbComponentsReceived[3] = {false, false, false}; // R, G, B reçus

// Buffer de réception série non bloquant
static char serialBuffer[48]; // lignes courtes
static uint8_t serialIndex = 0;

// Timing - servo avance d'un step toutes les minutes
unsigned long lastServoUpdate = 0;
const unsigned long stepInterval = 30UL * 1000UL;   // 30 secondes
const int step = 10;  // Steps fins de 10µs

void setup() {
  // Configuration série
  Serial.begin(9600);
  
  // Servo lib
  canvasServo.attach(servoPin);
  canvasServo.writeMicroseconds(pulseWidth);
  lastWrittenPulse = pulseWidth;

  // Configuration LED WS2812
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(100);
  
  // Couleur initiale (rouge)
  leds[0] = CRGB(rgbBuffer[0], rgbBuffer[1], rgbBuffer[2]);
  FastLED.show();

  // Initialisation timing
  lastServoUpdate = millis();
  
  Serial.println("Arduino servo + LED ready (mode temporel - 1 step par minute)");
}
void onIndexPulse() {
  // Fonction supprimée - plus de capteur
}

void loop() {
  unsigned long now = millis();

  // Gestion de la réception série (non bloquant)
  processSerialInput();

  // Gestion du servo
  updateServo(now);
  
  // Gestion de la séquence rainbow d'accueil
  if (rainbowSequence) {
    if (rainbowStart == 0) {
      rainbowStart = now; // Initialiser le début de la séquence
    }
    
    unsigned long rainbowElapsed = now - rainbowStart;
    if (rainbowElapsed < rainbowDuration) {
      // Calculer la couleur rainbow en fonction du temps
      uint8_t hue = (rainbowElapsed * 255) / rainbowDuration;
      leds[0] = CHSV(hue, 255, 255);
      FastLED.show();
    } else {
      // Fin de la séquence rainbow, passer à la couleur par défaut
      rainbowSequence = false;
      leds[0] = CRGB(rgbBuffer[0], rgbBuffer[1], rgbBuffer[2]);
      FastLED.show();
    }
  } else {
    // Mise à jour LED si nouvelles données RGB reçues (après la séquence)
    updateLED();
  }
}

void updateServo(unsigned long now) {
  // Avancement automatique toutes les minutes - gestion débordement millis()
  unsigned long elapsed = (unsigned long)(now - lastServoUpdate);
  
  if (elapsed >= stepInterval) {
    lastServoUpdate = now;
    
    // Calcul nouvelle position
    pulseWidth += direction * step;
    
    // Inversion direction si limites atteintes
    if (pulseWidth >= maxPulse || pulseWidth <= minPulse) {
      direction *= -1;
      if (pulseWidth < minPulse) pulseWidth = minPulse; 
      else if (pulseWidth > maxPulse) pulseWidth = maxPulse;
    }
    
    // Écriture seulement si changement
    if (pulseWidth != lastWrittenPulse) {
      canvasServo.writeMicroseconds(pulseWidth);
      lastWrittenPulse = pulseWidth;
    }
  }
}

// (plus de générateur manuel)

void updateLED() {
  if (newRGBReceived) {
    newRGBReceived = false;
    
    // Application directe et immédiate des nouvelles valeurs RGB
    leds[0] = CRGB(rgbBuffer[0], rgbBuffer[1], rgbBuffer[2]);
    FastLED.show();
  }
}

// ----------- Communication Série (non bloquante) ------------

static int fastAtoi(const char* &p) {
  int v = 0; bool any=false;
  while (*p >= '0' && *p <= '9') { v = v*10 + (*p - '0'); p++; any=true; }
  return any? v : -1; // -1 si aucun chiffre
}

void parseLine(const char* line) {
  // Ignore lignes vides / espaces en tête
  while (*line == ' ' || *line == '\t') line++;
  if (*line == '\0') return;

  // Format 1: rgb,r,g,b
  if (line[0]=='r' && line[1]=='g' && line[2]=='b' && line[3]==',') {
    const char* p = line + 4;
    int r = fastAtoi(p); if (*p==',') p++; else return;
    int g = fastAtoi(p); if (*p==',') p++; else return;
    int b = fastAtoi(p);
    if (r>=0 && g>=0 && b>=0) {
      updateRGBBuffer(r,g,b);
    }
    return;
  }

  // Format 2: r###g###b### (ordre strict)
  if (line[0]=='r') {
    const char* p = line+1; int r = fastAtoi(p);
    if (r>=0 && *p=='g') {
      p++; int g = fastAtoi(p);
      if (g>=0 && *p=='b') {
        p++; int b = fastAtoi(p);
        if (b>=0 && *p=='\0') { updateRGBBuffer(r,g,b); return; }
      }
    }
  }

  // Format 3: composante seule r### / g### / b###
  if ((line[0]=='r' || line[0]=='g' || line[0]=='b')) {
    const char* p = line+1; int v = fastAtoi(p);
    if (v>=0 && *p=='\0') {
      if (line[0]=='r') updateRGBComponent(0,v);
      else if (line[0]=='g') updateRGBComponent(1,v);
      else updateRGBComponent(2,v);
    }
  }
}

void processSerialInput() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      serialBuffer[serialIndex] = '\0';
  parseLine(serialBuffer);
      serialIndex = 0; // reset
    } else {
      if (serialIndex < sizeof(serialBuffer) - 1) {
        serialBuffer[serialIndex++] = c;
      } else { // overflow -> reset
        serialIndex = 0;
      }
    }
  }
}

// Met à jour une composante RGB et vérifie si le triplet est complet
void updateRGBComponent(uint8_t component, uint8_t value) {
  if (value > 255) value = 255; // value est signé dans fastAtoi > -1
  rgbBuffer[component] = (uint8_t)value;
  rgbComponentsReceived[component] = true;
  
  // Vérifier si toutes les composantes sont reçues
  if (rgbComponentsReceived[0] && rgbComponentsReceived[1] && rgbComponentsReceived[2]) {
    newRGBReceived = true;
    // Reset des flags
    rgbComponentsReceived[0] = false;
    rgbComponentsReceived[1] = false;
    rgbComponentsReceived[2] = false;
  }
}

// Met à jour le buffer RGB de manière atomique
void updateRGBBuffer(uint8_t r, uint8_t g, uint8_t b) {
  if (r>255) r=255; if (g>255) g=255; if (b>255) b=255; // garde-fous
  rgbBuffer[0] = r;
  rgbBuffer[1] = g;
  rgbBuffer[2] = b;
  newRGBReceived = true;
}