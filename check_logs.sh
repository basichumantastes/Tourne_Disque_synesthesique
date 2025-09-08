#!/bin/bash

# Script temporaire pour voir les logs Arduino
REMOTE_USER="blanchard"
REMOTE_HOST="192.168.0.114"
PASSWORD_FILE="/Users/blanchard/Library/CloudStorage/Dropbox/AUDIO PRO/PROJECTS/INSTALLATIONS/SANDRA/Tourne_Disque_synesthesique/.ssh_password"

if [ ! -f "${PASSWORD_FILE}" ]; then
    echo "Password file not found"
    exit 1
fi

SSH_PASSWORD=$(cat "${PASSWORD_FILE}")

echo "=== Checking Arduino Serial Logs ==="
sshpass -p "${SSH_PASSWORD}" ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "
    echo 'Derniers logs du service arduino_serial:'
    sudo journalctl -u arduino_serial.service --no-pager -n 50
"
