#!/usr/bin/env python3
"""
Arduino Serial Communication Service

Ce script gère la communication série avec l'Arduino et transmet les données
au système via OSC. Il fait partie du projet Tourne Disque Synesthésique.
"""

import os
import sys
import time
import serial
import json
import logging
import re
from pathlib import Path
from pythonosc import udp_client

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/blanchard/tourne_disque/logs/arduino_serial.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("arduino_serial")

class ArduinoSerialReader:
    """Classe pour gérer la lecture série depuis l'Arduino"""
    
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, osc_ip='127.0.0.1', osc_port=5005):
        self.port = port
        self.baudrate = baudrate
        self.osc_ip = osc_ip
        self.osc_port = osc_port
        self.serial = None
        self.osc_client = None
        self.connected = False
        
        # Statut actuel du système
        self.motor_speed = 0
        self.is_balancier_mode = False
        self.current_angle = 0
        
    def setup(self):
        """Configure la connexion série et le client OSC"""
        try:
            # Charger la configuration réseau
            parent_dir = Path(__file__).resolve().parent.parent
            network_config_path = os.path.join(parent_dir, 'network.json')
            
            with open(network_config_path, 'r') as f:
                config = json.load(f)
                # Utilise la configuration du router depuis network.json
                self.osc_ip = config['osc']['router']['ip']
                self.osc_port = config['osc']['router']['port']
            
            # Configurer le client OSC
            self.osc_client = udp_client.SimpleUDPClient(self.osc_ip, self.osc_port)
            logger.info(f"Client OSC configuré vers {self.osc_ip}:{self.osc_port}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration: {e}")
            return False
    
    def connect(self):
        """Établit la connexion série avec l'Arduino"""
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Attente pour l'initialisation de l'Arduino
            self.connected = True
            logger.info(f"Connecté à Arduino sur {self.port} à {self.baudrate} bauds")
            return True
        except serial.SerialException as e:
            logger.error(f"Erreur de connexion à l'Arduino: {e}")
            self.connected = False
            return False
    
    def reconnect(self):
        """Tente de rétablir la connexion en cas de perte"""
        logger.info("Tentative de reconnexion à l'Arduino...")
        if self.serial:
            try:
                self.serial.close()
            except:
                pass
        
        # Attendre avant de reconnecter
        time.sleep(5)
        return self.connect()
    
    def send_command(self, command):
        """Envoie une commande à l'Arduino"""
        if not self.connected or not self.serial:
            logger.error("Impossible d'envoyer la commande: non connecté")
            return False
            
        try:
            self.serial.write(f"{command}\n".encode())
            logger.info(f"Commande envoyée: {command}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de commande: {e}")
            self.connected = False
            return False
    
    def set_motor_speed(self, speed):
        """Change la vitesse du moteur"""
        return self.send_command(f"v{int(speed)}")
    
    def toggle_balancier(self):
        """Active/désactive le mode balancier"""
        return self.send_command("b")
    
    def read(self):
        """Lit les données de l'Arduino et les envoie via OSC"""
        if not self.connected or not self.serial:
            return False
        
        try:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8', errors='replace').strip()
                if line:
                    logger.debug(f"Reçu: {line}")
                    self.process_data(line)
            return True
        except serial.SerialException as e:
            logger.error(f"Erreur de lecture: {e}")
            self.connected = False
            return False
    
    def process_data(self, data):
        """Traite les données reçues de l'Arduino"""
        try:
            # Vitesse réglée
            speed_match = re.search(r"Vitesse réglée à :\s*(-?\d+)", data)
            if speed_match:
                speed = int(speed_match.group(1))
                self.motor_speed = speed
                logger.info(f"Vitesse du moteur: {speed}")
                self.osc_client.send_message("/arduino/motor/speed", speed)
                return
                
            # Nouvelle direction appliquée
            dir_match = re.search(r"Nouvelle direction appliquée, vitesse réglée à :\s*(-?\d+)", data)
            if dir_match:
                speed = int(dir_match.group(1))
                self.motor_speed = speed
                logger.info(f"Nouvelle direction du moteur: {speed}")
                self.osc_client.send_message("/arduino/motor/speed", speed)
                return
                
            # Mode balancier activé
            if "Mode balancier du servo activé" in data:
                self.is_balancier_mode = True
                logger.info("Mode balancier activé")
                self.osc_client.send_message("/arduino/servo/mode", 1)
                return
                
            # Servo déplacé
            servo_match = re.search(r"Servo déplacé à :\s*(\d+)", data)
            if servo_match:
                angle = int(servo_match.group(1))
                self.current_angle = angle
                logger.info(f"Angle du servo: {angle}")
                self.osc_client.send_message("/arduino/servo/angle", angle)
                return
                
            # Arrêt moteur
            if "Moteur arrêté" in data:
                self.motor_speed = 0
                logger.info("Moteur arrêté")
                self.osc_client.send_message("/arduino/motor/speed", 0)
                return
                
            # Commandes diverses (logging uniquement)
            if "Arrêt progressif demandé" in data:
                logger.info("Arrêt progressif demandé")
                
            if "Changement de direction demandé" in data:
                logger.info("Changement de direction demandé")
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement des données: {e}")
    
    def run(self):
        """Boucle principale"""
        if not self.setup():
            logger.error("Échec de la configuration, arrêt du service")
            return
        
        logger.info("Démarrage du service Arduino Serial")
        
        while True:
            if not self.connected:
                if not self.reconnect():
                    time.sleep(10)  # Attendre avant de réessayer
                    continue
            
            if not self.read():
                # Problème de lecture, tenter de reconnecter
                self.connected = False
                continue
            
            # Petit délai pour ne pas surcharger le CPU
            time.sleep(0.01)
    
    def close(self):
        """Ferme proprement les connexions"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info("Connexion série fermée")
            self.connected = False

# Point d'entrée principal
def main():
    logger.info("=== Démarrage du service de communication Arduino ===")
    arduino = ArduinoSerialReader()
    
    try:
        arduino.run()
    except KeyboardInterrupt:
        logger.info("Arrêt du service (interruption clavier)")
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
    finally:
        arduino.close()
        logger.info("Service arrêté")

if __name__ == "__main__":
    main()