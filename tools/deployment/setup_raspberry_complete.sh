#!/bin/bash
#
# Complete installation script for Raspberry Pi 5
# This script installs all necessary dependencies, including camera configuration
#

echo "=== COMPLETE INSTALLATION FOR RASPBERRY PI 5 ==="
echo "This script will configure the system and install all necessary dependencies."
echo

# System update
echo "=== System update ==="
sudo apt update
sudo apt upgrade -y

# Basic system dependencies installation
echo "=== Installing basic system dependencies ==="
sudo apt install -y \
    python3-venv \
    python3-pip \
    git \
    puredata \
    libcap-dev

# Camera dependencies installation for Raspberry Pi 5
echo "=== Installing camera dependencies ==="
sudo apt install -y python3-libcamera
sudo apt install -y python3-picamera2
sudo apt install -y libcamera-apps
sudo apt install -y python3-opencv
sudo apt install -y gstreamer1.0-plugins-base gstreamer1.0-plugins-good

# Arduino Support
echo "=== Installing Arduino CLI for Arduino integration ==="
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=~/.local/bin sh
# Add Arduino CLI to PATH if not already in the path
if ! grep -q "arduino-cli" ~/.bashrc; then
    echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc
    export PATH=$PATH:$HOME/.local/bin
fi

# Update Arduino CLI index
echo "=== Updating Arduino CLI index ==="
arduino-cli core update-index

# Install Arduino AVR core (for Arduino Uno)
echo "=== Installing Arduino AVR core ==="
arduino-cli core install arduino:avr

# Set permissions for serial port access
echo "=== Setting up serial port permissions ==="
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER

# Camera configuration for Raspberry Pi 5
echo "=== Camera configuration for Raspberry Pi 5 ==="
CONFIG_PATH="/boot/firmware/config.txt"

# Check if config.txt file exists
if [ -f "$CONFIG_PATH" ]; then
    echo "Configuring camera in $CONFIG_PATH"
    
    # Disable automatic camera detection which can cause problems
    if grep -q "camera_auto_detect=1" "$CONFIG_PATH"; then
        sudo sed -i 's/camera_auto_detect=1/camera_auto_detect=0/' "$CONFIG_PATH"
        echo "Automatic camera detection disabled (camera_auto_detect=0)"
        CAMERA_CONFIG_CHANGED=1
    elif ! grep -q "camera_auto_detect=" "$CONFIG_PATH"; then
        sudo sh -c "echo 'camera_auto_detect=0' >> $CONFIG_PATH"
        echo "Automatic camera detection disabled (camera_auto_detect=0)"
        CAMERA_CONFIG_CHANGED=1
    fi
    
    # Configure specifically for IMX219 camera (Camera Module v2) on CAM1 port
    if ! grep -q "dtoverlay=imx219,cam1" "$CONFIG_PATH"; then
        sudo sh -c "echo 'dtoverlay=imx219,cam1' >> $CONFIG_PATH"
        echo "Specific configuration for IMX219 camera on CAM1 port added"
        CAMERA_CONFIG_CHANGED=1
    fi
    
    # Disable HDMI audio output to force USB audio card usage
    echo "=== Disabling HDMI audio output ==="
    if ! grep -q "hdmi_ignore_edid_audio=1" "$CONFIG_PATH"; then
        sudo sh -c "echo 'hdmi_ignore_edid_audio=1' >> $CONFIG_PATH"
        echo "EDID audio disabled for HDMI"
        AUDIO_CONFIG_CHANGED=1
    fi
    
    if ! grep -q "dtparam=audio=off" "$CONFIG_PATH"; then
        sudo sh -c "echo 'dtparam=audio=off' >> $CONFIG_PATH"
        echo "On-board audio disabled"
        AUDIO_CONFIG_CHANGED=1
    fi
    
    if [ "$CAMERA_CONFIG_CHANGED" == "1" ] || [ "$AUDIO_CONFIG_CHANGED" == "1" ]; then
        echo "System configuration has been modified, a restart will be necessary."
    fi
else
    echo "WARNING: File $CONFIG_PATH does not exist. System configuration not performed."
fi

# Creating project folders and logs
echo "=== Preparing folder structure ==="
mkdir -p /home/blanchard/tourne_disque/logs

# Systemd services configuration
echo "=== Configuring systemd services ==="
if [ -d "/home/blanchard/tourne_disque/services" ]; then
    sudo cp /home/blanchard/tourne_disque/services/*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable osc_router.service
    sudo systemctl enable vision.service
    sudo systemctl enable logic.service
    sudo systemctl enable puredata.service
    sudo systemctl enable led_controller.service
    sudo systemctl enable music_engine.service
    echo "Systemd services configured successfully."
else
    echo "WARNING: Services folder does not exist yet. Services will be configured during deployment."
fi

# Python dependencies installation
echo "=== Installing Python dependencies ==="
if [ -f "/home/blanchard/tourne_disque/requirements.txt" ]; then
    cd /home/blanchard/tourne_disque
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Create bridge to system packages for accessing libcamera and other system libraries
    echo "=== Creating bridge to system packages for virtual environment ==="
    echo '/usr/lib/python3/dist-packages' > /home/blanchard/tourne_disque/venv/lib/python3.11/site-packages/system-packages.pth
    echo "Bridge to system packages created successfully."
    
    echo "Python dependencies installed successfully."
else
    echo "WARNING: requirements.txt file does not exist yet. Python dependencies will be installed during deployment."
fi

# Camera test
echo "=== Camera test ==="
if command -v libcamera-hello &> /dev/null; then
    echo "Testing camera with libcamera-hello (ignore errors if Pi hasn't been restarted yet)"
    libcamera-hello --list-cameras
    echo
    echo "Testing camera with picamera2 (ignore errors if Pi hasn't been restarted yet)"
    python3 -c "
try:
    from picamera2 import Picamera2
    picam2 = Picamera2()
    print('Camera correctly detected by picamera2')
    print(f'Camera properties: {picam2.camera_properties}')
except Exception as e:
    print(f'Error during camera test: {str(e)}')
"
else
    echo "The libcamera-hello command is not available. Check installation."
fi

echo
echo "=== CONFIGURATION SUMMARY ==="
echo "- System updated"
echo "- System dependencies installed"
echo "- Camera support for Raspberry Pi 5 installed"
echo "- Specific camera configuration established in /boot/firmware/config.txt"
echo "- Folder structure prepared"
echo "- Arduino CLI installed and configured"

if [ -d "/home/blanchard/tourne_disque/services" ]; then
    echo "- Systemd services configured"
else
    echo "- Systemd services: waiting for deployment"
fi

if [ -f "/home/blanchard/tourne_disque/requirements.txt" ]; then
    echo "- Python dependencies installed"
else
    echo "- Python dependencies: waiting for deployment"
fi

echo
echo "=== NEXT STEPS ==="
if [ "$CAMERA_CONFIG_CHANGED" == "1" ] || [ "$AUDIO_CONFIG_CHANGED" == "1" ]; then
    echo "1. IMPORTANT: Restart the Raspberry Pi to apply system configuration:"
    echo "   sudo reboot"
    echo "2. After restart, deploy the code with ./deploy.sh from your development machine"
else
    echo "1. Deploy the code with ./deploy.sh from your development machine"
    echo "2. Restart the Raspberry Pi to activate all services:"
    echo "   sudo reboot"
fi
echo
echo "Installation complete!"