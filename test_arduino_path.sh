#!/bin/bash

REMOTE_USER="blanchard"
REMOTE_HOST="192.168.0.114"
REMOTE_PATH="/home/blanchard/tourne_disque"
PASSWORD_FILE=".ssh_password"

# Check what files are actually on the Raspberry Pi
SSH_PASSWORD=$(cat "${PASSWORD_FILE}")
sshpass -p "${SSH_PASSWORD}" ssh ${REMOTE_USER}@${REMOTE_HOST} "
    echo 'Checking Arduino file structure on Raspberry Pi:'
    find ${REMOTE_PATH} -name 'main.ino' -type f
    echo ''
    echo 'Current working directory structure:'
    ls -la ${REMOTE_PATH}/src/
    echo ''
    echo 'Arduino directory structure:'
    ls -la ${REMOTE_PATH}/src/arduino/ 2>/dev/null || echo 'arduino directory not found'
"
