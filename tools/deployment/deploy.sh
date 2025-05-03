#!/bin/bash

# Vérification des arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <raspberry_pi_ip>"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

RASPBERRY_IP=$1
RASPBERRY_USER="pi"
PROJECT_NAME="tourne_disque"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE_DIR="/home/${RASPBERRY_USER}/${PROJECT_NAME}"

echo "🚀 Déploiement vers le Raspberry Pi (${RASPBERRY_IP})"

# Vérification de la connexion SSH
echo "📡 Test de la connexion SSH..."
ssh -q ${RASPBERRY_USER}@${RASPBERRY_IP} exit
if [ $? -ne 0 ]; then
    echo "❌ Impossible de se connecter au Raspberry Pi"
    exit 1
fi

# Création du dossier distant si nécessaire
echo "📁 Création du dossier distant..."
ssh ${RASPBERRY_USER}@${RASPBERRY_IP} "mkdir -p ${REMOTE_DIR}"

# Synchronisation des fichiers
echo "🔄 Synchronisation des fichiers..."
rsync -av --progress \
    --exclude '.git' \
    --exclude '.gitignore' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '.pio' \
    --exclude '.pioenvs' \
    --exclude '.piolibdeps' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude 'node_modules' \
    "${LOCAL_DIR}/" \
    "${RASPBERRY_USER}@${RASPBERRY_IP}:${REMOTE_DIR}/"

# Vérification du résultat
if [ $? -eq 0 ]; then
    echo "✅ Déploiement terminé avec succès!"
    echo "📍 Les fichiers ont été déployés dans: ${REMOTE_DIR}"
else
    echo "❌ Erreur lors du déploiement"
    exit 1
fi