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
            print(f"Client OSC configuré: {name} ({cfg['ip']}:{cfg['port']})")

        # Table de routage hiérarchique des messages - simplifiée par module source
        self.routes = {
            # Routage par module source (notation avec / à la fin indique préfixe)
            "/vision/": ["logic", "led", "dev"],     # Tous les messages vision vers logic, led et dev
            "/logic/": ["led", "puredata", "music_engine", "dev"],  # Messages logic vers LED, PD, music engine et dev
            "/music_engine/": ["logic", "puredata", "dev"],  # Messages music_engine vers logic, PD et dev
            "/arduino/": ["logic", "puredata", "dev"],  # Messages arduino vers logic, PD et dev
            
            # Cas spécifiques qui surchargent les règles générales (optionnel)
            #"/vision/color/raw/hsv": ["logic", "dev"],  # HSV vers logic et dev (surcharge du préfixe /vision/)
        }

        # Configuration du serveur OSC local
        self.dispatcher = dispatcher.Dispatcher()
        self.setup_routes()
        
        # Création du serveur
        self.server = osc_server.ThreadingOSCUDPServer(
            ("127.0.0.1", 5005),  # Port local pour recevoir les messages
            self.dispatcher
        )
        
        print("Table de routage OSC configurée:")
        for address, destinations in self.routes.items():
            print(f"  {address} → {', '.join(destinations)}")

    def setup_routes(self):
        """Configure un handler générique pour toutes les adresses possibles"""
        # Configuration d'un handler par défaut qui traitera tous les messages
        self.dispatcher.set_default_handler(self.handle_message)
        
    def handle_message(self, address, *args):
        """Handler qui route les messages selon le routage hiérarchique"""
        # Essayer d'abord de trouver une correspondance exacte
        if address in self.routes:
            destinations = self.routes[address]
            self._send_to_destinations(address, args, destinations)
            return
            
        # Si pas de correspondance exacte, essayer le matching par préfixe
        for prefix, destinations in self.routes.items():
            if prefix.endswith('/') and address.startswith(prefix):
                # Extraire le module source du pattern d'adresse
                parts = address.split('/')
                if len(parts) > 1:
                    source_module = parts[1]
                    print(f"Message de {source_module} routé par préfixe {prefix}: {address}")
                
                self._send_to_destinations(address, args, destinations)
                return
        
        # Aucune route trouvée, on utilise le comportement par défaut (broadcast)
        print(f"Aucune route configurée pour l'adresse: {address}")
        self._send_to_all_clients(address, args)
    
    def _send_to_destinations(self, address, args, destinations):
        """Méthode utilitaire pour envoyer un message aux destinations spécifiées"""
        for dest in destinations:
            if dest in self.clients:
                self.clients[dest].send_message(address, args)
            else:
                print(f"Destination inconnue dans la table de routage: {dest}")
                
    def _send_to_all_clients(self, address, args):
        """Méthode utilitaire pour diffuser un message à tous les clients"""
        print(f"Diffusion du message à tous les clients: {address}")
        for client in self.clients.values():
            client.send_message(address, args)

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