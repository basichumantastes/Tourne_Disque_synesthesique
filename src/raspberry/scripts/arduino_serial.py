#!/usr/bin/env python3
"""
Arduino Serial Communication Service

Ce script gère la communication série avec l'Arduino et transmet les données
au système via OSC. Il fait partie du projet Tourne Disque Synesthésique.
L'Arduino gère le servo balancier et reçoit les couleurs RGB via série USB.
"""

import os
import sys
import time
import serial
import json
import logging
import re
import threading
import colorsys
from pathlib import Path
from pythonosc import udp_client, dispatcher, osc_server

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

class ArduinoSerialController:
    """Classe pour gérer la communication série avec l'Arduino (servo + LED)"""
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.osc_client = None
        self.connected = False
        
        # Configuration OSC (sera chargée depuis network.json)
        self.osc_ip = None
        self.osc_port = None
        
        # Statut actuel du système
        self.is_balancier_mode = False
        self.current_angle = 0
        self.current_rgb = [255, 0, 0]  # RGB actuel
        
        # Buffer pour reconstituer RGB depuis les messages individuels
        self.rgb_components = {'r': 0, 'g': 0, 'b': 0}
        self.rgb_updated = {'r': False, 'g': False, 'b': False}
        
        # Configuration OSC
        self.dispatcher = None
        self.server = None
        
        # Paramètres de boost visuel (chargés depuis config.json)
        self.saturation_boost = 1.2   # Valeur par défaut
        self.contrast_boost = 1.1     # Valeur par défaut  
        self.brightness_boost = 1.1   # Valeur par défaut
        
        # Charger la configuration depuis config.json
        self.load_config()
        
    def load_config(self):
        """Charge la configuration depuis le fichier config.json"""
        try:
            parent_dir = Path(__file__).resolve().parent.parent
            config_path = os.path.join(parent_dir, 'config.json')
            
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Charger les paramètres de traitement des couleurs
            color_config = config.get('color_processing', {})
            self.saturation_boost = color_config.get('saturation_boost', 1.2)
            self.contrast_boost = color_config.get('contrast_boost', 1.1)
            self.brightness_boost = color_config.get('brightness_boost', 1.1)
            
            logger.info(f"Configuration chargée: saturation={self.saturation_boost}, "
                       f"contraste={self.contrast_boost}, luminosité={self.brightness_boost}")
                       
        except FileNotFoundError:
            logger.warning("Fichier config.json non trouvé, utilisation des valeurs par défaut")
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de format JSON dans config.json: {e}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
    
    def reload_config(self):
        """Recharge la configuration depuis config.json (utile pour ajustements en temps réel)"""
        logger.info("Rechargement de la configuration...")
        self.load_config()
        
    def setup(self):
        """Configure la connexion série, le client OSC et le serveur OSC"""
        try:
            # Charger la configuration réseau
            parent_dir = Path(__file__).resolve().parent.parent
            network_config_path = os.path.join(parent_dir, 'network.json')
            
            with open(network_config_path, 'r') as f:
                config = json.load(f)
                # Utilise la configuration du router depuis network.json
                self.osc_ip = config['osc']['router']['ip']
                self.osc_port = config['osc']['router']['port']
            
            # Configurer le client OSC pour envoyer des messages
            self.osc_client = udp_client.SimpleUDPClient(self.osc_ip, self.osc_port)
            logger.info(f"Client OSC configuré vers {self.osc_ip}:{self.osc_port}")
            
            # Configurer le serveur OSC pour recevoir les couleurs RGB
            self.setup_osc_server(config)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration: {e}")
            return False
    
    def setup_osc_server(self, config):
        """Configure le serveur OSC pour recevoir les données RGB"""
        self.dispatcher = dispatcher.Dispatcher()
        
        # Handlers pour recevoir les couleurs RGB brutes directement de vision.py
        self.dispatcher.map("/vision/color/raw/rgb/r", self.handle_vision_rgb_r)
        self.dispatcher.map("/vision/color/raw/rgb/g", self.handle_vision_rgb_g) 
        self.dispatcher.map("/vision/color/raw/rgb/b", self.handle_vision_rgb_b)
        
        # Handler pour recevoir les couleurs RGB lissées de logic.py (DÉSACTIVÉ pour éviter conflit)
        # self.dispatcher.map("/logic/color/smooth/rgb", self.handle_rgb_color)
        
        # Démarrer le serveur OSC
        arduino_config = config['osc']['arduino_serial']
        self.server = osc_server.ThreadingOSCUDPServer(
            (arduino_config['ip'], arduino_config['port']),
            self.dispatcher
        )
        
        # Démarrer le serveur dans un thread séparé
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        logger.info(f"Serveur OSC démarré sur {arduino_config['ip']}:{arduino_config['port']}")
    
    def boost_color_hsv(self, r, g, b):
        """Boost le contraste et la saturation via conversion HSV"""
        try:
            # Normaliser RGB (0-1)
            r_norm = r / 255.0
            g_norm = g / 255.0  
            b_norm = b / 255.0
            
            # Convertir RGB vers HSV
            h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
            
            # Appliquer le boost de saturation
            s_boosted = min(1.0, s * self.saturation_boost)
            
            # Appliquer le boost de luminosité/contraste
            v_boosted = min(1.0, v * self.brightness_boost)
            
            # Appliquer le contraste (étendre les valeurs autour de 0.5)
            v_contrasted = ((v_boosted - 0.5) * self.contrast_boost) + 0.5
            v_contrasted = max(0.0, min(1.0, v_contrasted))
            
            # Reconvertir HSV vers RGB
            r_boost, g_boost, b_boost = colorsys.hsv_to_rgb(h, s_boosted, v_contrasted)
            
            # Convertir vers entiers 0-255
            r_final = max(0, min(255, int(r_boost * 255)))
            g_final = max(0, min(255, int(g_boost * 255)))
            b_final = max(0, min(255, int(b_boost * 255)))
            
            return r_final, g_final, b_final
            
        except Exception as e:
            logger.error(f"Erreur lors du boost couleur HSV: {e}")
            # En cas d'erreur, retourner les valeurs originales
            return r, g, b
    
    def handle_vision_rgb_r(self, address, value):
        """Traite la composante R reçue directement de vision.py"""
        self.handle_vision_rgb_component('r', value)
    
    def handle_vision_rgb_g(self, address, value):
        """Traite la composante G reçue directement de vision.py"""
        self.handle_vision_rgb_component('g', value)
    
    def handle_vision_rgb_b(self, address, value):
        """Traite la composante B reçue directement de vision.py"""
        self.handle_vision_rgb_component('b', value)
    
    def handle_vision_rgb_component(self, component, value):
        """Traite une composante RGB individuelle et reconstitue le RGB complet"""
        try:
            # Convertir et contraindre la valeur
            rgb_value = max(0, min(255, int(value)))
            
            # Mettre à jour le buffer de cette composante
            self.rgb_components[component] = rgb_value
            self.rgb_updated[component] = True
            
            # Si toutes les composantes ont été mises à jour, envoyer à l'Arduino
            if all(self.rgb_updated.values()):
                r = self.rgb_components['r']
                g = self.rgb_components['g'] 
                b = self.rgb_components['b']
                
                # Appliquer le boost de contraste et saturation via HSV
                r_boosted, g_boosted, b_boosted = self.boost_color_hsv(r, g, b)
                
                # Envoyer à l'Arduino en un seul message RGB complet
                self.send_rgb_complete_to_arduino(r_boosted, g_boosted, b_boosted)
                self.current_rgb = [r_boosted, g_boosted, b_boosted]
                
                # Reset des flags de mise à jour
                self.rgb_updated = {'r': False, 'g': False, 'b': False}
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement RGB vision: {e}")
    
    def send_rgb_complete_to_arduino(self, r, g, b):
        """Envoie les valeurs RGB complètes à l'Arduino en un seul message"""
        if not self.connected or not self.serial:
            logger.warning("Impossible d'envoyer RGB: Arduino non connecté")
            return False
            
        try:
            # Format: "rgb,255,128,64\n" (un seul message pour éviter le clignotement)
            command = f"rgb,{r},{g},{b}\n"
            self.serial.write(command.encode())
            
            # Envoyer aussi via OSC vers le dev pour monitoring
            if self.osc_client:
                self.osc_client.send_message("/arduino/serial/rgb", [r, g, b])
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi RGB complet: {e}")
            self.connected = False
            return False
    
    def handle_rgb_color(self, address, r, g, b):
        """Traite les couleurs RGB lissées reçues de logic.py (fallback)"""
        try:
            # Convertir en entiers et contraindre
            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))
            
            self.current_rgb = [r, g, b]
            
            # Envoyer à l'Arduino via série (message complet)
            self.send_rgb_complete_to_arduino(r, g, b)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement RGB lissé: {e}")
    
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
    
    def toggle_balancier(self):
        """Active/désactive le mode balancier (si cette fonctionnalité existe encore)"""
        return self.send_command("b")
    
    def read(self):
        """Lit les données de l'Arduino et les envoie via OSC"""
        if not self.connected or not self.serial:
            return False
        
        try:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8', errors='replace').strip()
                if line:
                    self.process_data(line)
            return True
        except serial.SerialException as e:
            logger.error(f"Erreur de lecture: {e}")
            self.connected = False
            return False
    
    def process_data(self, data):
        """Traite les données reçues de l'Arduino (servo et LED)"""
        try:
            # Arduino ready
            if "Arduino servo + LED ready" in data:
                logger.info("Arduino prêt (servo + LED)")
                return
                
            # RGB mis à jour
            if "RGB updated:" in data:
                return
                
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
        if self.server:
            self.server.shutdown()
            logger.info("Serveur OSC fermé")
            
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info("Connexion série fermée")
            self.connected = False

# Point d'entrée principal
def main():
    logger.info("=== Démarrage du service de communication Arduino (servo + LED) ===")
    arduino = ArduinoSerialController()
    
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