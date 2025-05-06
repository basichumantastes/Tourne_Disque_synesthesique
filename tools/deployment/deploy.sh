#!/bin/bash

# Configuration
REMOTE_USER="blanchard"
REMOTE_HOST="192.168.0.124"
REMOTE_PATH="/home/blanchard/tourne_disque"
LOCAL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Fonction pour afficher les messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Vérification de la connexion SSH
log "Vérification de la connexion SSH..."
if ! ssh -q ${REMOTE_USER}@${REMOTE_HOST} exit; then
    log "Erreur: Impossible de se connecter au Raspberry Pi"
    exit 1
fi

# Synchronisation des fichiers
log "Déploiement des fichiers vers le Raspberry Pi..."
rsync -avz --exclude '.git/' \
           --exclude '*.pyc' \
           --exclude '__pycache__' \
           --exclude 'venv' \
           --exclude '.env' \
           --exclude 'logs' \
           "${LOCAL_PATH}/src/raspberry/" \
           "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"

if [ $? -eq 0 ]; then
    log "Déploiement réussi"
else
    log "Erreur lors du déploiement"
    exit 1
fi

# Redémarrage des services systemd
log "Redémarrage des services..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "sudo systemctl restart vision.service logic.service puredata.service"

log "Déploiement terminé avec succès"