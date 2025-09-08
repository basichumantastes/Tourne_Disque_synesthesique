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
- Optionally upload Arduino code
- Configure and restart services

```bash
# Deploy Python code only (default)
./tools/deployment/deploy.sh

# Deploy with Arduino code upload
./tools/deployment/deploy.sh --with-arduino
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
- `arduino_serial.service`: Communication with Arduino controller

## Arduino Integration

The Arduino component provides mechanical control and visual feedback:

### Hardware
- **Arduino Uno** connected via USB serial
- **Servo motor**: 180° 25kg servo (Pin 9)
- **WS2812 LED**: Single pixel indicator (Pin 6)
- **Power**: External 5V supply for servo and LED

### Features
- **Automatic canvas rotation**: Every 30 seconds with 10µs PWM steps
- **Welcome sequence**: 5-second rainbow LED animation on startup  
- **Color display**: Shows colors detected by vision system
- **Serial communication**: Receives RGB commands at 9600 baud

### Deployment
Arduino code is automatically compiled and uploaded when using:
```bash
./tools/deployment/deploy.sh --with-arduino
```

### Monitoring
```bash
# Check Arduino service status
sudo systemctl status arduino_serial.service

# View Arduino communication logs
sudo journalctl -u arduino_serial.service -n 50

# Check connected Arduino
ls -l /dev/tty*
```

## Arduino Integration

### Setup
Arduino integration requires Arduino CLI on the Raspberry Pi. The deployment script automatically installs it, but you can also install manually:
```bash
# Check if Arduino CLI is installed
arduino-cli version

# Manual installation if needed
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
sudo mv bin/arduino-cli /usr/local/bin/
arduino-cli config init
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli lib install FastLED Servo
```

### Uploading Code
The deployment script handles Arduino upload automatically:
```bash
# Automatic upload with deployment
./tools/deployment/deploy.sh --with-arduino
```

Manual upload process:
```bash
# Create temporary sketch directory
mkdir -p /tmp/arduino_sketch
cp /home/blanchard/tourne_disque/src/arduino/platformio/src/main.ino /tmp/arduino_sketch/arduino_sketch.ino
cd /tmp/arduino_sketch

# Compile and upload
arduino-cli compile --fqbn arduino:avr:uno .
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno .
```

### Serial Communication
The `arduino_serial.service` handles communication between Raspberry Pi and Arduino:
```bash
# Monitor serial communication
sudo journalctl -u arduino_serial.service -f

# Check Arduino connection
ls -l /dev/tty*
```

### Arduino Features
- **Canvas rotation**: Automatic servo movement every 30 seconds
- **Welcome sequence**: 5-second rainbow LED animation on boot
- **Color feedback**: Displays colors detected by vision system
- **RGB commands**: Supports multiple color format inputs

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