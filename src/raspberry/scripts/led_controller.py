#!/usr/bin/env python3

"""
Contrôleur pour le bandeau LED
- Reçoit les couleurs via OSC
- Applique les couleurs au bandeau LED
"""

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
    def __init__(self, clk_pin=16, dat_pin=20):
        self.led_strip = LEDStrip(clk_pin, dat_pin)
        
        # Chargement de la configuration depuis le nouveau chemin
        network_config_path = os.path.join(parent_dir, 'network.json')
        with open(network_config_path, 'r') as f:
            self.config = json.load(f)
        
        # Configuration OSC
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map("/color/rgb", self.handle_rgb_color)
        # Ajout d'un handler pour les messages RGB bruts
        self.dispatcher.map("/color/raw/rgb", self.handle_rgb_color)
        
        # Serveur OSC
        osc_config = self.config['osc']['led']
        self.server = osc_server.ThreadingOSCUDPServer(
            (osc_config['ip'], osc_config['port']),
            self.dispatcher
        )
        
    def handle_rgb_color(self, address, r, g, b):
        """Gestion des couleurs RGB reçues via OSC"""
        self.led_strip.setcolourrgb(int(r), int(g), int(b))
        print(f"LED couleur appliquée depuis {address}: R={r}, G={g}, B={b}")
        
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