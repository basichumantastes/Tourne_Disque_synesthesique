#!/bin/bash

# Configuration
REMOTE_USER="blanchard"
REMOTE_HOST="192.168.0.114"
REMOTE_PATH="/home/blanchard/tourne_disque"
LOCAL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Password file (at the project root)
PASSWORD_FILE="${LOCAL_PATH}/.ssh_password"

# Function to display messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Parse command-line arguments
SKIP_SETUP=0
ARDUINO_UPLOAD=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-setup)
            SKIP_SETUP=1
            shift
            ;;
        --with-arduino)
            ARDUINO_UPLOAD=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-setup] [--with-arduino]"
            exit 1
            ;;
    esac
done

# Confirmation log
if [ "$ARDUINO_UPLOAD" -eq 0 ]; then
    log "Deploying without Arduino functionality"
else
    log "Deploying with Arduino functionality enabled"
fi

# Check if password file exists
if [ ! -f "${PASSWORD_FILE}" ]; then
    log "Error: The .ssh_password file does not exist at the project root."
    log "Create this file with your SSH password and ensure it is protected (chmod 600)."
    exit 1
fi

# Read password from file
SSH_PASSWORD=$(cat "${PASSWORD_FILE}")

# Disable SSH agent completely
unset SSH_AUTH_SOCK
unset SSH_AGENT_PID

# Direct SSH options without key management
SSH_OPTS="-o PreferredAuthentications=password -o PubkeyAuthentication=no -o IdentitiesOnly=no"

# Use sshpass to automate password entry
if ! command -v sshpass &> /dev/null; then
    log "The 'sshpass' program is not installed. Installing..."
    brew install hudochenkov/sshpass/sshpass || { log "Error installing sshpass. Please install it manually."; exit 1; }
fi

# Verify SSH connection with sshpass
log "Checking SSH connection..."
sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} "echo 'SSH connection established'"
    
if [ $? -ne 0 ]; then
    log "Error: Cannot connect to Raspberry Pi"
    exit 1
fi

# Check if target directory exists on Raspberry Pi
log "Checking target directory..."
sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} ${REMOTE_USER}@${REMOTE_HOST} "[ -d '${REMOTE_PATH}' ]"
if [ $? -ne 0 ]; then
    log "Error: Directory ${REMOTE_PATH} does not exist on Raspberry Pi."
    log "Please configure the Raspberry Pi first by running the setup_raspberry_complete.sh script"
    log "See README.md for complete installation instructions."
    exit 1
fi

# Synchronize files with sshpass
log "Deploying files to Raspberry Pi..."
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
    log "Files deployed successfully"
else
    log "Error deploying files"
    exit 1
fi

# Install Python dependencies (update only)
log "Updating Python dependencies..."
sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} ${REMOTE_USER}@${REMOTE_HOST} "
    # Install system dependencies required for Python packages
    sudo apt install -y libcap-dev
    
    # Install libcamera dependencies required for picamera2
    sudo apt install -y python3-libcamera libcamera-apps python3-picamera2
    
    cd ${REMOTE_PATH} 
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Ensure picamera2 is explicitly installed in the venv
    pip install picamera2
"

# Upload Arduino code if requested
if [ "$ARDUINO_UPLOAD" -eq 1 ]; then
    log "Uploading Arduino code..."
    sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_PATH}/src/arduino/platformio
        
        # Check if Arduino is connected
        if [ -e /dev/ttyACM0 ]; then
            # Compile and upload Arduino code
            arduino-cli compile --fqbn arduino:avr:uno .
            arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno .
            echo 'Arduino code uploaded successfully'
        else
            echo 'Arduino not detected at /dev/ttyACM0, skipping upload'
        fi
    "
else
    log "Skipping Arduino code upload as requested"
fi

# Install and restart systemd services
log "Updating services..."
sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} ${REMOTE_USER}@${REMOTE_HOST} "
    # Copy all service files to systemd
    sudo cp ${REMOTE_PATH}/services/*.service /etc/systemd/system/
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable all services (to start at boot)
    for service in ${REMOTE_PATH}/services/*.service; do
        service_name=\$(basename \$service)
        sudo systemctl enable \$service_name
    done
    
    # Restart all services except arduino_serial if Arduino upload wasn't requested
    sudo systemctl restart osc_router.service vision.service logic.service puredata.service led_controller.service music_engine.service
    
    # Only restart arduino_serial service if Arduino upload was requested
    if [ \"$ARDUINO_UPLOAD\" -eq 1 ]; then
        sudo systemctl restart arduino_serial.service
    else
        log \"Skipping arduino_serial.service restart\"
        # Make sure arduino_serial service is stopped to avoid errors
        sudo systemctl stop arduino_serial.service
    fi
"

# Check services status
log "Checking services status..."
sshpass -p "${SSH_PASSWORD}" ssh ${SSH_OPTS} ${REMOTE_USER}@${REMOTE_HOST} "
    echo '=== OSC Router Status ==='
    sudo systemctl status osc_router.service | head -n 5
    
    echo '=== Music Engine Status ==='
    sudo systemctl status music_engine.service | head -n 5
    
    echo '=== Logic Status ==='
    sudo systemctl status logic.service | head -n 5
    
    echo '=== LED Controller Status ==='
    sudo systemctl status led_controller.service | head -n 5
    
    echo '=== PureData Status ==='
    sudo systemctl status puredata.service | head -n 5
    
    echo '=== Vision Status ==='
    sudo systemctl status vision.service | head -n 5
    
    # Only show arduino_serial status if it was requested
    if [ \"$ARDUINO_UPLOAD\" -eq 1 ]; then
        echo '=== Arduino Serial Status ==='
        sudo systemctl status arduino_serial.service | head -n 5
    else
        echo '=== Arduino Serial Status ==='
        echo 'Service not started (Arduino upload was not requested)'
    fi
"

log "Deployment completed successfully"