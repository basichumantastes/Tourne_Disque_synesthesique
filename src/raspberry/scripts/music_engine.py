#!/usr/bin/env python3
# music_engine.py
# ✨ Rôle : simple squelette — écoute les messages OSC "/event"
# envoyés par logic.py et les affiche. Aucune logique musicale pour l'instant.

"""
music_engine.py
---------------
• Communique avec le routeur OSC central (osc_router.py)
• Écoute l'adresse '/event' 
• ⤷ La fonction ne fait qu'imprimer l'événement reçu
• Possibilité d'envoyer des messages à d'autres modules via le routeur OSC
"""

import json
import os
import sys
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
import time

def load_network_config():
    """Charge la configuration réseau depuis network.json."""
    try:
        # Chemin relatif pour remonter d'un niveau depuis scripts/ vers le répertoire parent
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        config_path = os.path.join(parent_dir, "network.json")
        
        with open(config_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration réseau: {e}")
        sys.exit(1)

def handle_event(address, *args):
    """Fonction stub qui affiche simplement les événements OSC reçus."""
    print(f"Événement reçu sur {address}: {args}")

def main():
    """Fonction principale qui initialise la communication avec le routeur OSC."""
    # Charger la configuration réseau
    config = load_network_config()
    
    # Configuration pour recevoir les messages du routeur OSC
    local_ip = "127.0.0.1"
    local_port = 9003  # Port pour recevoir les messages du routeur OSC
    
    # Créer un client pour envoyer des messages au routeur OSC
    router_client = udp_client.SimpleUDPClient("127.0.0.1", 5005)
    
    # Créer un dispatcher pour gérer les messages OSC
    dispatcher = Dispatcher()
    dispatcher.map("/event", handle_event)
    
    # Configurer et démarrer le serveur OSC local
    server = ThreadingOSCUDPServer((local_ip, local_port), dispatcher)
    print(f"Moteur musical démarré sur {local_ip}:{local_port}")
    print("En attente d'événements OSC sur l'adresse '/event'...")
    
    # Envoyer un message au routeur OSC pour s'enregistrer
    router_client.send_message("/register/music_engine", local_port)
    print("Enregistré auprès du routeur OSC central")
    
    # Exemple d'envoi périodique d'un message au routeur (à des fins de débogage)
    # try:
    #     while True:
    #         router_client.send_message("/music/status", "alive")
    #         time.sleep(10)
    # except KeyboardInterrupt:
    #     print("Arrêt du moteur musical...")
    
    # Boucle infinie pour recevoir les messages
    server.serve_forever()

if __name__ == "__main__":
    main()