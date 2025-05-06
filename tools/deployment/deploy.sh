#!/bin/bash

# Configuration
REMOTE_USER="blanchard"
REMOTE_HOST="192.168.0.124"
REMOTE_PATH="/home/blanchard/tourne_disque"
LOCAL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Fichier contenant le mot de passe (à la racine du projet)
PASSWORD_FILE="${LOCAL_PATH}/.ssh_password"

# Fonction pour afficher les messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Vérifier si le fichier de mot de passe existe
if [ ! -f "${PASSWORD_FILE}" ]; then
    log "Erreur: Le fichier .ssh_password n'existe pas à la racine du projet."
    log "Créez ce fichier avec votre mot de passe SSH et assurez-vous qu'il est protégé (chmod 600)."
    exit 1
fi

# Lire le mot de passe depuis le fichier
SSH_PASSWORD=$(cat "${PASSWORD_FILE}")

# Désactiver l'utilisation de SSH agent complètement
unset SSH_AUTH_SOCK
unset SSH_AGENT_PID

# Options SSH directes sans gestion de clés
SSH_OPTS="-o PreferredAuthentications=password -o PubkeyAuthentication=no -o IdentitiesOnly=no"

# Utiliser sshpass pour automatiser la saisie du mot de passe
if ! command -v sshpass &> /dev/null; then
    log "Le programme 'sshpass' n'est pas installé. Installation en cours..."
    brew install hudochenkov/sshpass/sshpass || { log "Erreur lors de l'installation de sshpass. Veuillez l'installer manuellement."; exit 1; }
fi

# Vérification de la connexion SSH avec sshpass
log "Vérification de la connexion SSH..."
sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} "echo 'Connexion SSH établie'"
    
if [ $? -ne 0 ]; then
    log "Erreur: Impossible de se connecter au Raspberry Pi"
    exit 1
fi

# Synchronisation des fichiers avec sshpass
log "Déploiement des fichiers vers le Raspberry Pi..."
sshpass -p "${SSH_PASSWORD}" rsync -avz --exclude '.git/' \
           --exclude '*.pyc' \
           --exclude '__pycache__' \
           --exclude 'venv' \
           --exclude '.env' \
           --exclude 'logs' \
           -e "ssh ${SSH_OPTS}" \
           "${LOCAL_PATH}/src/raspberry/" \
           "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"

if [ $? -eq 0 ]; then
    log "Déploiement réussi"
else
    log "Erreur lors du déploiement"
    exit 1
fi

# Installation des dépendances Python avec sshpass
log "Installation des dépendances Python..."
sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

# Installation et redémarrage des services systemd avec sshpass
log "Installation et redémarrage des services..."
sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} ${REMOTE_USER}@${REMOTE_HOST} "
    # Copier tous les fichiers de service vers systemd
    sudo cp ${REMOTE_PATH}/services/*.service /etc/systemd/system/
    
    # Recharger systemd
    sudo systemctl daemon-reload
    
    # Activer tous les services (pour qu'ils démarrent au boot)
    for service in ${REMOTE_PATH}/services/*.service; do
        service_name=\$(basename \$service)
        sudo systemctl enable \$service_name
    done
    
    # Redémarrer tous les services
    sudo systemctl restart osc_router.service vision.service logic.service puredata.service led_controller.service music_engine.service
"

# Pour vérifier l'état des services
log "Vérification du statut des services..."
sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} ${REMOTE_USER}@${REMOTE_HOST} "
    echo '=== Statut de OSC Router ==='
    sudo systemctl status osc_router.service | head -n 5
    
    echo '=== Statut de Music Engine ==='
    sudo systemctl status music_engine.service | head -n 5
    
    echo '=== Statut de Logic ==='
    sudo systemctl status logic.service | head -n 5
    
    echo '=== Statut de LED Controller ==='
    sudo systemctl status led_controller.service | head -n 5
    
    echo '=== Statut de PureData ==='
    sudo systemctl status puredata.service | head -n 5
    
    echo '=== Statut de Vision ==='
    sudo systemctl status vision.service | head -n 5
"

log "Déploiement terminé avec succès"