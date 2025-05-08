# Raspberry Pi Configuration

## Overview
This directory contains the software that runs on the Raspberry Pi for the Synesthetic Turntable project. The system uses computer vision to detect objects on a turntable and generates corresponding music and LED lighting.

## System Components
- **Vision Module**: Captures and analyzes video feed from the camera
- **Logic Module**: Coordinates system components and manages state
- **OSC Router**: Handles Open Sound Control communication between components
- **Music Engine**: Generates and controls sound based on detected objects
- **LED Controller**: Manages LED strip visualization
- **Pure Data**: Real-time audio processing environment

## Installation Process

The installation is now managed through two deployment scripts:

### 1. Initial Raspberry Pi Setup
Run the `setup_raspberry_complete.sh` script on the Raspberry Pi to:
- Install system dependencies (OpenCV, PureData, Python packages)
- Configure the camera module
- Prepare the folder structure
- Set up systemd services

```bash
# On the Raspberry Pi
cd /path/to/project
./tools/deployment/setup_raspberry_complete.sh
```

### 2. Code Deployment
From your development machine, use the `deploy.sh` script to:
- Transfer files to the Raspberry Pi
- Install Python dependencies
- Configure and restart services

```bash
# On your development machine
cd /path/to/project
./tools/deployment/deploy.sh
```

## Hardware Configuration

### Camera
- Model: Raspberry Pi Camera v2 (IMX219)
- Connection: Via CAM1 port on Raspberry Pi
- Position: Adjusted to frame the detection area

### LED Strip
- Connection: Via GPIO pins according to the configuration in `ledstrip.py`
- Power: External 5V power supply

## Services

The following systemd services are automatically installed and configured:

- `vision.service`: Camera capture and image analysis
- `logic.service`: Core application logic and coordination
- `osc_router.service`: OSC message handling
- `music_engine.service`: Sound generation
- `led_controller.service`: LED strip control
- `puredata.service`: Audio processing

## Arduino Integration

### Setup
Arduino integration requires Arduino CLI on the Raspberry Pi:
```bash
# Check if Arduino CLI is installed
arduino-cli version

# If not installed, install it
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
```

### Uploading Code
To upload code to an Arduino connected to the Raspberry Pi:
```bash
# Compile and upload Arduino sketch
arduino-cli compile --fqbn arduino:avr:uno /path/to/sketch
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno /path/to/sketch
```

### Serial Communication
Monitor serial output from Arduino:
```bash
arduino-cli monitor -p /dev/ttyACM0
```

### Troubleshooting
- Check Arduino connection: `ls -l /dev/tty*`
- Permission issues: `sudo usermod -a -G dialout $USER`
- If upload fails, try: `sudo chmod 666 /dev/ttyACM0`

## Troubleshooting

### Service Status
Check service status with:
```bash
systemctl status [service-name].service
```

### Logs
View detailed logs with:
```bash
journalctl -u [service-name].service -n 100 --no-pager
```

### Camera
- Test camera: `libcamera-hello --list-cameras`
- Check camera config: `cat /boot/firmware/config.txt | grep camera`

### Network
- OSC communication uses the network configuration in `network.json`
- Verify connectivity with: `ping [destination-ip]`