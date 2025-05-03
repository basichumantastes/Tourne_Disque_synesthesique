#!/usr/bin/env python3
"""
Module principal pour le projet Tourne Disque Synesthésique.
Gère la communication entre le Raspberry Pi et l'Arduino.
"""

import os
import time
import logging
from logging.handlers import RotatingFileHandler
import serial
from dotenv import load_dotenv

# Configuration du logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'tourne_disque.log')

logger = logging.getLogger('tourne_disque')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Chargement des variables d'environnement
load_dotenv()

class ArduinoCommunication:
    """Gère la communication série avec l'Arduino."""
    
    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        """Initialise la communication série avec l'Arduino."""
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        
    def connect(self):
        """Établit la connexion avec l'Arduino."""
        try:
            self.serial = serial.Serial(self.port, self.baudrate)
            logger.info(f"Connexion établie avec l'Arduino sur {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Erreur de connexion à l'Arduino: {e}")
            return False
            
    def send_command(self, command):
        """Envoie une commande à l'Arduino."""
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(f"{command}\n".encode())
                logger.debug(f"Commande envoyée: {command}")
                return True
            except serial.SerialException as e:
                logger.error(f"Erreur d'envoi de commande: {e}")
                return False
        return False
        
    def read_response(self):
        """Lit la réponse de l'Arduino."""
        if self.serial and self.serial.is_open:
            try:
                response = self.serial.readline().decode().strip()
                logger.debug(f"Réponse reçue: {response}")
                return response
            except serial.SerialException as e:
                logger.error(f"Erreur de lecture: {e}")
        return None

def main():
    """Fonction principale."""
    logger.info("Démarrage du programme Tourne Disque Synesthésique")
    
    arduino = ArduinoCommunication()
    if not arduino.connect():
        logger.error("Impossible de se connecter à l'Arduino")
        return
    
    try:
        while True:
            # Boucle principale
            # TODO: Implémenter la logique spécifique au projet
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Arrêt du programme")
    finally:
        if arduino.serial:
            arduino.serial.close()
            logger.info("Connexion Arduino fermée")

if __name__ == "__main__":
    main()