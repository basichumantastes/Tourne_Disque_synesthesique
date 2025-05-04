#!/bin/bash

# Configuration
LOCAL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NETWORK_CONFIG="${LOCAL_PATH}/config/network.json"

# Lecture de l'IP depuis le fichier de configuration
REMOTE_IP=$(jq -r '.raspberry_receiver.ip' "$NETWORK_CONFIG")
if [ -z "$REMOTE_IP" ] || [ "$REMOTE_IP" == "null" ]; then
    echo "Erreur: L'adresse IP du raspberry_receiver n'est pas configurée dans network.json"
    exit 1
fi

REMOTE_USER="blanchard"
REMOTE_PATH="/home/blanchard"

# Fonction pour afficher les messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Vérification de la connexion SSH
log "Vérification de la connexion SSH..."
if ! ssh -q ${REMOTE_USER}@${REMOTE_IP} exit; then
    log "Erreur: Impossible de se connecter au Raspberry Pi"
    exit 1
fi

# Création des dossiers nécessaires
log "Création des dossiers sur le Raspberry Pi..."
ssh ${REMOTE_USER}@${REMOTE_IP} "mkdir -p ~/puredata"

# Synchronisation des fichiers Pure Data
log "Déploiement des patches Pure Data..."
rsync -avz "${LOCAL_PATH}/src/raspberry_receiver/puredata/" \
           "${REMOTE_USER}@${REMOTE_IP}:${REMOTE_PATH}/puredata/"

# Installation du service systemd
log "Installation du service Pure Data..."
sudo_commands="sudo cp ~/puredata.service /etc/systemd/system/ && \
               sudo systemctl daemon-reload && \
               sudo systemctl enable puredata.service && \
               sudo systemctl restart puredata.service"

# Copie du service
scp "${LOCAL_PATH}/src/raspberry_receiver/services/puredata.service" \
    "${REMOTE_USER}@${REMOTE_IP}:${REMOTE_PATH}/puredata.service"

# Exécution des commandes sudo
ssh ${REMOTE_USER}@${REMOTE_IP} "${sudo_commands}"

log "Déploiement terminé avec succès"