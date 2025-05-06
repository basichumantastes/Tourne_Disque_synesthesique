#!/bin/bash

# Mise à jour du système
sudo apt update
sudo apt upgrade -y

# Installation des dépendances système
sudo apt install -y \
    python3-venv \
    python3-pip \
    python3-opencv \
    libcamera-dev \
    puredata \
    git

# Configuration des services systemd
sudo cp /home/blanchard/tourne_disque/services/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable osc_router.service
sudo systemctl enable vision.service
sudo systemctl enable logic.service
sudo systemctl enable puredata.service
sudo systemctl enable led_controller.service
sudo systemctl enable music_engine.service

# Création du dossier pour le projet
mkdir -p /home/blanchard/tourne_disque/logs

# Installation des dépendances Python
cd /home/blanchard/tourne_disque
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Installation terminée ! Redémarrez le Raspberry Pi pour activer tous les services."