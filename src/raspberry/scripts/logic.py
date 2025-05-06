#!/usr/bin/env python3

from pythonosc import udp_client, dispatcher, osc_server
import collections
import threading
import time
import json
import os
from pathlib import Path

# Chemin parent pour accéder à network.json
parent_dir = Path(__file__).resolve().parent.parent

# Configuration
COLOR_BUFFER_SIZE = 5
EMA_ALPHA = 0.0005

class OSCManager:
    def __init__(self):
        network_config_path = os.path.join(parent_dir, 'network.json')
        with open(network_config_path, 'r') as f:
            self.config = json.load(f)
        
        # Création des clients OSC
        osc_config = self.config['osc']
        self.puredata_client = udp_client.SimpleUDPClient(
            osc_config['puredata']['ip'],
            osc_config['puredata']['port']
        )
        self.led_client = udp_client.SimpleUDPClient(
            osc_config['led']['ip'],
            osc_config['led']['port']
        )
        
    def send_to_puredata(self, address, value):
        """Envoie un message OSC à Pure Data"""
        self.puredata_client.send_message(address, value)
        
    def send_to_leds(self, address, values):
        """Envoie un message OSC au contrôleur LED"""
        self.led_client.send_message(address, values)

class ColorProcessor:
    def __init__(self):
        # Gestionnaire OSC
        self.osc = OSCManager()
        
        # Buffers circulaires pour RGB
        self.rgb_buffers = {
            'r': collections.deque(maxlen=COLOR_BUFFER_SIZE),
            'g': collections.deque(maxlen=COLOR_BUFFER_SIZE),
            'b': collections.deque(maxlen=COLOR_BUFFER_SIZE)
        }
        
        # Variables EMA
        self.rgb_ema = {'r': None, 'g': None, 'b': None}
        self.hsv_ema = {'h': None, 's': None, 'v': None}
        
        # Initialisation des buffers RGB
        for buffer in self.rgb_buffers.values():
            for _ in range(COLOR_BUFFER_SIZE):
                buffer.append(0)
        
        # Configuration OSC server
        self.setup_osc_server()

    def setup_osc_server(self):
        """Configure le serveur OSC pour recevoir les données de vision.py"""
        network_config_path = os.path.join(parent_dir, 'network.json')
        with open(network_config_path, 'r') as f:
            config = json.load(f)
            
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map("/color/raw/rgb", self.handle_rgb)
        self.dispatcher.map("/color/raw/hsv", self.handle_hsv)
        
        self.server = osc_server.ThreadingOSCUDPServer(
            (config['osc']['logic']['ip'], config['osc']['logic']['port']),
            self.dispatcher
        )

    def update_ema(self, current, new_value):
        """Calcule la nouvelle valeur EMA"""
        if current is None:
            return new_value
        return EMA_ALPHA * new_value + (1 - EMA_ALPHA) * current

    def handle_rgb(self, address, r, g, b):
        """Traitement des données RGB reçues"""
        # Mise à jour des buffers
        for value, color in zip([r, g, b], ['r', 'g', 'b']):
            self.rgb_buffers[color].append(value)
        
        # Calcul des moyennes et EMA
        rgb_smooth = {}
        for color in ['r', 'g', 'b']:
            # Moyenne du buffer
            avg = sum(self.rgb_buffers[color]) / len(self.rgb_buffers[color])
            # Mise à jour EMA
            self.rgb_ema[color] = self.update_ema(self.rgb_ema[color], avg)
            rgb_smooth[color] = int(self.rgb_ema[color])
        
        # Envoi au contrôleur LED
        self.osc.send_to_leds("/color/rgb", [
            rgb_smooth['r'],
            rgb_smooth['g'],
            rgb_smooth['b']
        ])
        
        # Envoi à Pure Data
        for color, value in rgb_smooth.items():
            self.osc.send_to_puredata(f"/color/rgb/{color}", value)

    def handle_hsv(self, address, h, s, v):
        """Traitement des données HSV reçues"""
        # Mise à jour des EMA HSV
        hsv_smooth = {}
        for value, param in zip([h, s, v], ['h', 's', 'v']):
            self.hsv_ema[param] = self.update_ema(self.hsv_ema[param], value)
            hsv_smooth[param] = int(self.hsv_ema[param])
            
            # Envoi à Pure Data
            self.osc.send_to_puredata(
                f"/color/hsv/{param}",
                hsv_smooth[param]
            )

    def run(self):
        """Démarre le serveur OSC"""
        print("Module de logique démarré - Écoute sur le port 9001")
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\nArrêt du module de logique")

def main():
    processor = ColorProcessor()
    processor.run()

if __name__ == "__main__":
    main()