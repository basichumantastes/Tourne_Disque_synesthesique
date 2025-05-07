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
    puredata

# Camera dependencies installation for Raspberry Pi 5
echo "=== Installing camera dependencies ==="
sudo apt install -y python3-libcamera
sudo apt install -y python3-picamera2
sudo apt install -y libcamera-apps
sudo apt install -y python3-opencv
sudo apt install -y gstreamer1.0-plugins-base gstreamer1.0-plugins-good

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
    
    if [ "$CAMERA_CONFIG_CHANGED" == "1" ]; then
        echo "Camera configuration has been modified, a restart will be necessary."
    fi
else
    echo "WARNING: File $CONFIG_PATH does not exist. Camera configuration not performed."
fi

# Creating project folders and logs
echo "=== Preparing folder structure ==="
mkdir -p /home/blanchard/tourne_disque/logs
mkdir -p /home/blanchard/tourne_disque/tools/deployment

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
if [ "$CAMERA_CONFIG_CHANGED" == "1" ]; then
    echo "1. IMPORTANT: Restart the Raspberry Pi to apply camera configuration:"
    echo "   sudo reboot"
    echo "2. After restart, deploy the code with ./deploy.sh from your development machine"
else
    echo "1. Deploy the code with ./deploy.sh from your development machine"
    echo "2. Restart the Raspberry Pi to activate all services:"
    echo "   sudo reboot"
fi
echo
echo "Installation complete!"