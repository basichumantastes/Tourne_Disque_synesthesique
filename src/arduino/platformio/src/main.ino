#include <AccelStepper.h>
#include <Servo.h>

#define MOTOR_INTERFACE_TYPE 1

// Création de l'objet stepper sur les broches STEP (9) et DIR (8)
AccelStepper stepper(MOTOR_INTERFACE_TYPE, 9, 8);

// Création de l'objet servo
Servo monServo;
const int SERVO_PIN = 3;  // Le servo est connecté sur D3

// Commande actuelle (vitesse maximale en pas/s, signe = sens)
long currentCmd = 100;
bool pendingStop = false;
bool pendingDirChange = false;
long newCmd = 100;

// Mode balancier (Servo)
bool balancierMode = false;
int angleMin = 80;  // Angle minimum du balancier
int angleMax = 100; // Angle maximum du balancier
int currentAngle = angleMin;
bool balancierDirection = true; // Direction du mouvement
unsigned long lastServoUpdate = 0;
const int SERVO_DELAY = 1000; // Temps entre chaque mise à jour du servo (1 sec)

// Constantes pour le fonctionnement du stepper
const long CONTINUOUS_INCREMENT = 1000000;
const long UPDATE_THRESHOLD = 100000;
const long POSITION_RESET_THRESHOLD = 1000000;

void resetPositions() {
  long currentPos = stepper.currentPosition();
  if (abs(currentPos) > POSITION_RESET_THRESHOLD) {
    long targetPos = stepper.targetPosition();
    stepper.setCurrentPosition(0);
    stepper.moveTo(targetPos - currentPos);
  }
}

void setup() {
  Serial.begin(9600);

  stepper.setAcceleration(50);
  stepper.setMaxSpeed(abs(currentCmd));
  if (currentCmd >= 0) {
    stepper.moveTo(stepper.currentPosition() + CONTINUOUS_INCREMENT);
  } else {
    stepper.moveTo(stepper.currentPosition() - CONTINUOUS_INCREMENT);
  }

  // Initialisation du servo
  monServo.attach(SERVO_PIN);
  monServo.write(angleMin);

  Serial.println("Commande moteur active :");
  Serial.println("- Tapez 'v' suivi d'un nombre (ex: v100, v-100, v0 pour arrêt)");
  Serial.println("- Tapez 'b' pour activer le mode balancier du servo.");
}

void loop() {
  // Lecture des commandes série
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("v")) {  // Commande de vitesse du stepper
      long incomingCmd = input.substring(1).toInt();
      balancierMode = false; // Désactiver le mode balancier du servo si commande moteur

      if (incomingCmd == 0 && currentCmd != 0) {
        pendingStop = true;
        newCmd = 0;
        stepper.stop();
        Serial.println("Arrêt progressif demandé...");
      } 
      else if (incomingCmd != 0 && ((incomingCmd > 0 && currentCmd < 0) || (incomingCmd < 0 && currentCmd > 0))) {
        pendingDirChange = true;
        newCmd = incomingCmd;
        stepper.stop();
        Serial.println("Changement de direction demandé, décélération...");
      } 
      else {
        currentCmd = incomingCmd;
        pendingStop = false;
        pendingDirChange = false;
        stepper.setMaxSpeed(abs(currentCmd));
        if (currentCmd > 0)
          stepper.moveTo(stepper.currentPosition() + CONTINUOUS_INCREMENT);
        else
          stepper.moveTo(stepper.currentPosition() - CONTINUOUS_INCREMENT);
        Serial.print("Vitesse réglée à : ");
        Serial.println(currentCmd);
      }
    } 
    else if (input == "b") {  // Activation du mode balancier (servo)
      balancierMode = true;
      Serial.println("Mode balancier du servo activé.");
    }
  }

  // Gestion du balancier du servo
  if (balancierMode) {
    if (millis() - lastServoUpdate > SERVO_DELAY) {
      lastServoUpdate = millis();
      
      // Changement d'angle
      if (balancierDirection) {
        currentAngle = angleMax;
      } else {
        currentAngle = angleMin;
      }
      balancierDirection = !balancierDirection;
      
      // Déplacement du servo
      monServo.write(currentAngle);
      Serial.print("Servo déplacé à : ");
      Serial.println(currentAngle);
    }
  }

  // Gestion du stepper
  if ((pendingStop || pendingDirChange) && abs(stepper.speed()) < 1) {
    currentCmd = newCmd;
    pendingStop = false;
    pendingDirChange = false;
    stepper.setMaxSpeed(abs(currentCmd));
    
    if (currentCmd == 0) {
      stepper.moveTo(stepper.currentPosition());
      Serial.println("Moteur arrêté.");
    } else {
      if (currentCmd > 0)
        stepper.moveTo(stepper.currentPosition() + CONTINUOUS_INCREMENT);
      else
        stepper.moveTo(stepper.currentPosition() - CONTINUOUS_INCREMENT);
      Serial.print("Nouvelle direction appliquée, vitesse réglée à : ");
      Serial.println(currentCmd);
    }
  }

  if (!pendingStop && !pendingDirChange && currentCmd != 0) {
    if (currentCmd > 0 && stepper.distanceToGo() < UPDATE_THRESHOLD)
      stepper.moveTo(stepper.targetPosition() + CONTINUOUS_INCREMENT);
    else if (currentCmd < 0 && stepper.distanceToGo() > -UPDATE_THRESHOLD)
      stepper.moveTo(stepper.targetPosition() - CONTINUOUS_INCREMENT);
  }

  resetPositions();
  stepper.run();
}