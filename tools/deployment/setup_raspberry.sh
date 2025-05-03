#!/bin/bash

# Configuration de l'environnement Python sur le Raspberry Pi
# À exécuter une seule fois lors de la première installation

# Mise à jour du système
sudo apt update
sudo apt upgrade -y

# Installation des dépendances système
sudo apt install -y \
    python3-venv \
    python3-pip \
    libcamera-dev \
    supervisor \
    git

# Configuration de l'environnement Python
cd /home/blanchard/color_detection_project
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances Python
pip install -r requirements/dev-requirements.txt

# Configuration de Supervisor
sudo cp src/raspberry/supervisor.conf /etc/supervisor/conf.d/tourne_disque.conf
sudo supervisorctl reread
sudo supervisorctl update

# Création du dossier de logs
mkdir -p logs

echo "Installation terminée !"