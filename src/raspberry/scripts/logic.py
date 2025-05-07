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
        
        # Client OSC unique pour le routeur central
        self.router_client = udp_client.SimpleUDPClient("127.0.0.1", 5005)
        print("Connexion établie avec le routeur OSC central sur 127.0.0.1:5005")
        
    def send_to_puredata(self, address, value):
        """Envoie un message OSC au routeur pour PureData"""
        self.router_client.send_message(address, value)
        
    def send_to_leds(self, address, values):
        """Envoie un message OSC au routeur pour le contrôleur LED"""
        self.router_client.send_message(address, values)

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
        
        # Compatibilité avec les anciens formats (liste complète RGB et HSV)
        self.dispatcher.map("/vision/color/raw/rgb", self.handle_rgb)
        self.dispatcher.map("/vision/color/raw/hsv", self.handle_hsv)
        
        # Nouveaux handlers pour les composantes individuelles RGB
        self.dispatcher.map("/vision/color/raw/rgb/r", self.handle_rgb_r)
        self.dispatcher.map("/vision/color/raw/rgb/g", self.handle_rgb_g)
        self.dispatcher.map("/vision/color/raw/rgb/b", self.handle_rgb_b)
        
        # Nouveaux handlers pour les composantes individuelles HSV
        self.dispatcher.map("/vision/color/raw/hsv/h", self.handle_hsv_h)
        self.dispatcher.map("/vision/color/raw/hsv/s", self.handle_hsv_s)
        self.dispatcher.map("/vision/color/raw/hsv/v", self.handle_hsv_v)
        
        self.server = osc_server.ThreadingOSCUDPServer(
            (config['osc']['logic']['ip'], config['osc']['logic']['port']),
            self.dispatcher
        )

    def update_ema(self, current, new_value):
        """Calcule la nouvelle valeur EMA"""
        if current is None:
            return new_value
        return EMA_ALPHA * new_value + (1 - EMA_ALPHA) * current

    # Handlers pour les composantes individuelles de RGB
    def handle_rgb_r(self, address, value):
        """Traitement de la composante R reçue individuellement"""
        self.process_rgb_component('r', value)
    
    def handle_rgb_g(self, address, value):
        """Traitement de la composante G reçue individuellement"""
        self.process_rgb_component('g', value)
    
    def handle_rgb_b(self, address, value):
        """Traitement de la composante B reçue individuellement"""
        self.process_rgb_component('b', value)
        
    def process_rgb_component(self, component, value):
        """Traite une composante RGB individuelle et envoie si toutes sont mises à jour"""
        # Mise à jour du buffer pour cette composante
        self.rgb_buffers[component].append(value)
        
        # Calcul de la moyenne et EMA pour cette composante
        avg = sum(self.rgb_buffers[component]) / len(self.rgb_buffers[component])
        self.rgb_ema[component] = self.update_ema(self.rgb_ema[component], avg)
        
        # Envoi à Pure Data pour cette composante spécifique
        smoothed_value = int(self.rgb_ema[component])
        self.osc.send_to_puredata(f"/logic/color/ema/{component}", smoothed_value)
        
        # NOTE: On n'envoie plus les valeurs EMA au contrôleur LED
        # Le contrôleur LED reçoit directement les valeurs brutes du module vision

    # Handlers pour les composantes individuelles de HSV
    def handle_hsv_h(self, address, value):
        """Traitement de la composante H reçue individuellement"""
        self.process_hsv_component('h', value)
    
    def handle_hsv_s(self, address, value):
        """Traitement de la composante S reçue individuellement"""
        self.process_hsv_component('s', value)
    
    def handle_hsv_v(self, address, value):
        """Traitement de la composante V reçue individuellement"""
        self.process_hsv_component('v', value)
    
    def process_hsv_component(self, component, value):
        """Traite une composante HSV individuelle"""
        # Mise à jour EMA pour cette composante
        self.hsv_ema[component] = self.update_ema(self.hsv_ema[component], value)
        smoothed_value = int(self.hsv_ema[component])
        
        # Envoi à Pure Data pour cette composante spécifique
        self.osc.send_to_puredata(f"/logic/color/ema/{component}", smoothed_value)

    # Handlers existants pour la compatibilité avec les anciens formats
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
        
        # NOTE: On n'envoie plus les valeurs EMA au contrôleur LED
        # Le contrôleur LED reçoit directement les valeurs brutes du module vision
        
        # Envoi à Pure Data avec nouveau format d'adressage
        for color, value in rgb_smooth.items():
            self.osc.send_to_puredata(f"/logic/color/ema/{color}", value)

    def handle_hsv(self, address, h, s, v):
        """Traitement des données HSV reçues"""
        # Mise à jour des EMA HSV
        hsv_smooth = {}
        for value, param in zip([h, s, v], ['h', 's', 'v']):
            self.hsv_ema[param] = self.update_ema(self.hsv_ema[param], value)
            hsv_smooth[param] = int(self.hsv_ema[param])
            
            # Envoi à Pure Data avec nouveau format d'adressage
            self.osc.send_to_puredata(
                f"/logic/color/ema/{param}",
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