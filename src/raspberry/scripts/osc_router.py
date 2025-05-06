#!/usr/bin/env python3

from pythonosc import udp_client, dispatcher, osc_server
import json
import argparse
from threading import Thread
import asyncio
import os
from pathlib import Path

class OSCRouter:
    def __init__(self):
        # Chemin parent pour accéder à network.json
        parent_dir = Path(__file__).resolve().parent.parent
        network_config_path = os.path.join(parent_dir, 'network.json')
        
        # Chargement de la configuration
        with open(network_config_path, 'r') as f:
            self.config = json.load(f)
        
        # Création des clients OSC pour chaque destination
        self.clients = {}
        for name, cfg in self.config['osc'].items():
            self.clients[name] = udp_client.SimpleUDPClient(
                cfg['ip'],
                cfg['port']
            )

        # Stockage des modules enregistrés avec leurs ports
        self.registered_modules = {}

        # Configuration du serveur OSC local
        self.dispatcher = dispatcher.Dispatcher()
        self.setup_routes()
        
        # Création du serveur
        self.server = osc_server.ThreadingOSCUDPServer(
            ("127.0.0.1", 5005),  # Port local pour recevoir les messages des autres scripts
            self.dispatcher
        )

    def setup_routes(self):
        """Configure les routes OSC"""
        # Routes pour les données de vision
        self.dispatcher.map("/color/raw/rgb", self.handle_rgb)
        self.dispatcher.map("/color/raw/hsv", self.handle_hsv)
        
        # Routes pour les données de logic
        self.dispatcher.map("/motion/speed", self.handle_speed)
        self.dispatcher.map("/motion/direction", self.handle_direction)
        
        # Route pour les événements génériques
        self.dispatcher.map("/event", self.handle_event)
        
        # Route pour l'enregistrement des modules
        self.dispatcher.map("/register/music_engine", self.register_music_engine)

    def route_message(self, address, *args):
        """Route un message vers toutes les destinations configurées"""
        for client in self.clients.values():
            client.send_message(address, args[0])

    # Handlers pour chaque type de message
    def handle_rgb(self, address, *args):
        self.route_message("/color/raw/rgb", args)

    def handle_hsv(self, address, *args):
        self.route_message("/color/raw/hsv", args)

    def handle_speed(self, address, *args):
        self.route_message("/motion/speed", args)

    def handle_direction(self, address, *args):
        self.route_message("/motion/direction", args)
        
    def handle_event(self, address, *args):
        """Gère les événements génériques"""
        self.route_message("/event", args)
        # Si le moteur musical est enregistré, lui envoyer directement le message
        if "music_engine" in self.registered_modules:
            port = self.registered_modules["music_engine"]
            client = udp_client.SimpleUDPClient("127.0.0.1", port)
            client.send_message("/event", args)

    def register_music_engine(self, address, *args):
        """Enregistre le port du moteur musical"""
        if args and len(args) > 0:
            port = int(args[0])
            self.registered_modules["music_engine"] = port
            print(f"Module music_engine enregistré sur le port {port}")

    def run(self):
        """Démarre le serveur OSC"""
        print("Démarrage du router OSC...")
        print(f"En écoute sur {self.server.server_address}")
        self.server.serve_forever()

def main():
    router = OSCRouter()
    router.run()

if __name__ == "__main__":
    main()