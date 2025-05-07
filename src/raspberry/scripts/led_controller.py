#!/usr/bin/env python3

"""
Contrôleur pour le bandeau LED
- Reçoit les couleurs via OSC
- Applique les couleurs au bandeau LED
"""

# Configuration des pins GPIO
CLK_PIN = 16  # Pin d'horloge pour le bandeau LED
DAT_PIN = 20  # Pin de données pour le bandeau LED

from pythonosc import dispatcher, osc_server
import threading
import sys
import os
from pathlib import Path

# Ajout du dossier parent au path pour permettre l'importation de lib.ledstrip
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from lib.ledstrip import LEDStrip
import json

class LEDController:
    def __init__(self):
        self.led_strip = LEDStrip(CLK_PIN, DAT_PIN)
        
        # Chargement de la configuration depuis le nouveau chemin
        network_config_path = os.path.join(parent_dir, 'network.json')
        with open(network_config_path, 'r') as f:
            self.config = json.load(f)
        
        # Configuration OSC
        self.dispatcher = dispatcher.Dispatcher()
        
        # Écouter les composantes RGB individuelles provenant du module vision
        self.dispatcher.map("/vision/color/raw/rgb/r", self.handle_rgb_r)
        self.dispatcher.map("/vision/color/raw/rgb/g", self.handle_rgb_g)
        self.dispatcher.map("/vision/color/raw/rgb/b", self.handle_rgb_b)
        
        # Stockage des valeurs RGB actuelles
        self.current_rgb = {'r': 0, 'g': 0, 'b': 0}
        
        # Serveur OSC
        osc_config = self.config['osc']['led']
        self.server = osc_server.ThreadingOSCUDPServer(
            (osc_config['ip'], osc_config['port']),
            self.dispatcher
        )
        
    def handle_rgb_r(self, address, r):
        """Gestion de la composante R reçue via OSC"""
        self.current_rgb['r'] = int(r)
        self.update_led_color()
        print(f"LED couleur R appliquée: R={r}")
        
    def handle_rgb_g(self, address, g):
        """Gestion de la composante G reçue via OSC"""
        self.current_rgb['g'] = int(g)
        self.update_led_color()
        print(f"LED couleur G appliquée: G={g}")
        
    def handle_rgb_b(self, address, b):
        """Gestion de la composante B reçue via OSC"""
        self.current_rgb['b'] = int(b)
        self.update_led_color()
        print(f"LED couleur B appliquée: B={b}")
        
    def update_led_color(self):
        """Met à jour la couleur du bandeau LED"""
        self.led_strip.setcolourrgb(
            self.current_rgb['r'],
            self.current_rgb['g'],
            self.current_rgb['b']
        )
        
    def run(self):
        """Démarre le serveur OSC"""
        print(f"LED Controller démarré sur CLK={self.led_strip._LEDStrip__clock}, DAT={self.led_strip._LEDStrip__data}")
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.cleanup()
            
    def cleanup(self):
        """Nettoyage des ressources"""
        if hasattr(self, 'led_strip'):
            self.led_strip.cleanup()

def main():
    controller = LEDController()
    controller.run()

if __name__ == "__main__":
    main()