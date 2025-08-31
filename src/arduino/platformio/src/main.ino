#include <Arduino.h>
#include <FastLED.h>

// Configuration servo (pilotage manuel des impulsions, non bloquant)
const int servoPin = 9;          // Broche PWM servo
volatile int pulseWidth = 500;   // Largeur d'impulsion actuelle (µs)
const int minPulse = 500;        // Ajuster selon servo (souvent 500-2400)
const int maxPulse = 2500;
const int step = 10;             // µs par étape de déplacement
int direction = 1;               // +1 ou -1
// Générateur d'impulsions non bloquant
static unsigned long frameStartMicros = 0; // début de la fenêtre de 20 ms
static unsigned long pulseStartMicros = 0; // début impulsion HIGH
static bool pulseHigh = false;            // état HIGH en cours
const unsigned long framePeriod = 20000UL; // 20 ms

// Capteur index (impulsion LOW par tour de roue crantée)
// Définir la broche utilisée (ex: 2 ou 3 sur UNO/Nano pour interruption externe)
const int indexSensorPin = 2;            // Adapter si nécessaire
volatile uint8_t revolutionPending = 0;   // Pulses en attente de traitement dans loop
volatile unsigned long lastIndexMicros = 0; // Pour anti-rebond / anti-double comptage
// Délai minimum entre deux impulsions valides (en µs) pour filtrer parasites
const unsigned long indexDebounceUs = 3000; // 3 ms (adapter selon capteur)
// Nombre de tours stepper pour un tour de toile (et donc 1 "step" servo)
const uint8_t REVOLUTIONS_PER_SERVO_STEP = 3;
uint8_t revolutionAccumulator = 0;         // Accumule jusqu'à 3 tours
// Si le capteur n'est pas branché, on retombe sur le mode temporel après un timeout
unsigned long lastRevolutionTime = 0;       // en ms
// Timeout pour considérer le capteur absent (aucune impulsion reçue)
const unsigned long sensorPresenceTimeout = 5000; // 5 s
bool sensorPresent = false;                // Deviendra true après première impulsion valide

// (Plus de Servo lib) Conservation du couple: on génère une impulsion à chaque trame 20 ms.
unsigned long lastServoMoveMs = 0; // pour debug éventuel / logs

// Configuration LED WS2812
#define LED_PIN 6
#define NUM_LEDS 1
CRGB leds[NUM_LEDS];

// Configuration communication série
volatile bool newRGBReceived = false;
volatile uint8_t rgbBuffer[3] = {255, 0, 0}; // Rouge par défaut
volatile bool rgbComponentsReceived[3] = {false, false, false}; // R, G, B reçus

// Buffer de réception série non bloquant
static char serialBuffer[48]; // lignes courtes
static uint8_t serialIndex = 0;

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

// ISR dédiée (lambda supprimée pour compatibilité AVR)
void onIndexPulse();

void setup() {
  // Configuration série
  Serial.begin(9600);
  
  // Servo manuel
  pinMode(servoPin, OUTPUT);
  digitalWrite(servoPin, LOW);
  frameStartMicros = micros();
  pulseHigh = false;
  lastServoMoveMs = millis();

  // Configuration LED WS2812
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(100);
  
  // Couleur initiale (rouge)
  leds[0] = CRGB(rgbBuffer[0], rgbBuffer[1], rgbBuffer[2]);
  FastLED.show();

  // Position initiale mémorisée (pulseWidth déjà défini)
  startTime = millis();
  state = WAIT_AT_BOTTOM;

  // Configuration capteur index
  // 74HC00 -> sortie push-pull maintenue HIGH, impulsion LOW brève : pas de pull-up interne nécessaire
  pinMode(indexSensorPin, INPUT); // Front descendant détecté via FALLING
  attachInterrupt(digitalPinToInterrupt(indexSensorPin), onIndexPulse, FALLING);
  lastRevolutionTime = millis();

  Serial.println("Index sensor initialized (attachInterrupt)");
  
  Serial.println("Arduino servo + LED ready");
}
void onIndexPulse() {
  unsigned long now = micros();
  if (now - lastIndexMicros > indexDebounceUs) {
    lastIndexMicros = now;
    if (revolutionPending < 250) {
      revolutionPending++;
    }
  }
}

void loop() {
  unsigned long now = millis();

  // Gestion de la réception série (non bloquant)
  processSerialInput();

  // Gestion du servo
  updateServo(now);
  
  // Mise à jour LED si nouvelles données RGB reçues
  updateLED();
  // Génération non bloquante de la trame servo (maintien du couple sans lib Servo)
  runServoPulseGenerator();
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
      {
        bool doStep = false;

        // Traitement des impulsions index accumulées
        if (revolutionPending > 0) {
          noInterrupts();
          uint8_t localPulses = revolutionPending;
          revolutionPending = 0;
          interrupts();

          sensorPresent = true;
          lastRevolutionTime = now;
          revolutionAccumulator += localPulses;

          if (revolutionAccumulator >= REVOLUTIONS_PER_SERVO_STEP) {
            revolutionAccumulator -= REVOLUTIONS_PER_SERVO_STEP; // garde surplus éventuel
            doStep = true;
          }
        } else {
          // Fallback timing si capteur absent ou perdu
          if (!sensorPresent || (now - lastRevolutionTime > sensorPresenceTimeout)) {
            if (now - lastServoUpdate >= stepInterval) {
              lastServoUpdate = now;
              doStep = true;
            }
            if (sensorPresent && (now - lastRevolutionTime > sensorPresenceTimeout)) {
              sensorPresent = false;
              revolutionAccumulator = 0; // reset pour cohérence
              Serial.println("Index sensor lost -> fallback timing mode");
            }
          }
        }

        if (doStep) {
          pulseWidth += direction * step;
          if (pulseWidth >= maxPulse || pulseWidth <= minPulse) {
            direction *= -1;
            if (pulseWidth < minPulse) pulseWidth = minPulse; else if (pulseWidth > maxPulse) pulseWidth = maxPulse;
          }
          // On ne fait qu'ajuster pulseWidth; la génération se fait en continu
          // (aucun appel bloquant).
          // pulseWidth est lue par runServoPulseGenerator() dans la trame suivante.
          if (sensorPresent) {
            Serial.print("Servo step (after ");
            Serial.print(REVOLUTIONS_PER_SERVO_STEP);
            Serial.print(" revolutions) -> pulse: ");
          } else {
            Serial.print("Servo step via timer fallback -> pulse: ");
          }
            Serial.println(pulseWidth);
          lastServoMoveMs = millis();
        }
      }
      break;

    default:
      break;
  }
}

// ---------------- Servo Pulse Generator (manuel) ----------------
// Génère une impulsion HIGH de 'pulseWidth' µs toutes les ~20 ms.
// Non bloquant : s'appuie sur micros().
void runServoPulseGenerator() {
  unsigned long now = micros();

  if (pulseHigh) {
    // Fin de l'impulsion ?
    if ((unsigned long)(now - pulseStartMicros) >= (unsigned long)pulseWidth) {
      digitalWrite(servoPin, LOW);
      pulseHigh = false;
      // Le reste de la fenêtre 20 ms est LOW.
    }
  } else {
    // Démarrer une nouvelle trame ?
    if ((unsigned long)(now - frameStartMicros) >= framePeriod) {
      frameStartMicros += framePeriod; // évite la dérive cumulée
      // Sécurité si retard important (> 1 frame): réaligner
      if ((unsigned long)(now - frameStartMicros) > framePeriod) {
        frameStartMicros = now; // réalignement dur
      }
      // Lancer l'impulsion HIGH
      digitalWrite(servoPin, HIGH);
      pulseStartMicros = now;
      pulseHigh = true;
    }
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
  if (r>255) r=255; if (g>255) g=255; if (b>255) b=255;
  if (r<0) r=0; if (g<0) g=0; if (b<0) b=0;
  rgbBuffer[0] = (uint8_t)r;
  rgbBuffer[1] = (uint8_t)g;
  rgbBuffer[2] = (uint8_t)b;
  newRGBReceived = true;
}