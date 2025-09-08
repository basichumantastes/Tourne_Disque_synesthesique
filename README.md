# Synesthetic Turntable - Interactive Installation

## Overview

Interactive artistic installation transforming colored circular canvases into synesthetic visual and sound experiences. The system analyzes colors from a rotating canvas in real-time, generates corresponding music, and synchronizes immersive LED lighting.

### Artistic concept
1. **Visual reading**: A camera analyzes colors from a continuously rotating circular canvas
2. **Sound translation**: Chromatic data feeds a generative music engine (Pure Data)
3. **Light translation**: An LED halo instantly reproduces perceived colors
4. **Synesthesia**: Each canvas becomes a unique score creating a multi-sensory experience

## Technical architecture

### Hardware components
- **Raspberry Pi 5**: Central image processing and coordination unit
- **Camera**: Raspberry Pi Camera Module v2 (IMX219) for color capture
- **Arduino Uno**: Mechanical controller for canvas rotation
  - **180° Servo**: 25kg motor for automatic rotation (30s/10µs steps)
  - **WS2812 LED**: Individual pixel for visual feedback and welcome sequence
- **LED Strip**: Neopixel ring for main light feedback
- **Mechanical support**: Structure to hold circular canvases

### Modular software architecture

The system uses a distributed architecture based on OSC (Open Sound Control):

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│             │────▶│                  │────▶│              │
│  vision.py  │ OSC │  osc_router.py   │ OSC │  logic.py    │
│ (capture)   │     │ (port 5005)      │     │ (process)    │
└─────────────┘     │                  │     └──────────────┘
                    │                  │           │
                    │                  │           ▼
                    │                  │     ┌──────────────┐
                    │                  │────▶│  PureData    │
                    │                  │     │ (audio)      │
                    │                  │     └──────────────┘
                    │                  │
┌─────────────┐     │                  │     ┌──────────────┐
│led_ctrl.py  │◀────│                  │────▶│arduino_serial│
│ (LEDs)      │     │                  │     │ (mechanics)  │
└─────────────┘     └──────────────────┘     └──────────────┘
```

## Detailed software modules

### 🎥 **Vision (`vision.py`)**
**Role**: Real-time capture and color analysis
- **Capture**: Uses `libcamera` and `cv2` for high-quality capture
- **Analysis**: Dominant color extraction with spatial averaging
- **Output**: OSC transmission of RGB/HSV values at 10Hz
- **Configuration**: Supports CLI arguments and `network.json` file

```python
# OSC messages sent
/vision/color/raw/rgb/r  # Red component (0-255)
/vision/color/raw/rgb/g  # Green component (0-255) 
/vision/color/raw/rgb/b  # Blue component (0-255)
/vision/color/raw/hsv/h  # Hue (0-360)
/vision/color/raw/hsv/s  # Saturation (0-255)
/vision/color/raw/hsv/v  # Value/brightness (0-255)
```

### 🎛️ **OSC Router (`osc_router.py`)**
**Role**: Central hub for inter-module communication
- **Architecture**: Central server on port 5005
- **Routing**: Hierarchical routing table by source module
- **Distribution**: Automatic distribution to configured destinations
- **Monitoring**: Logs all transiting messages

```python
# Main routing table
routes = {
    "/vision/": ["logic", "led", "puredata", "arduino_serial"],
    "/logic/": ["led", "puredata", "music_engine", "arduino_serial"],
    "/arduino/": ["logic", "puredata"]
}
```

### 🧠 **Business Logic (`logic.py`)**
**Role**: Color data processing and coordination
- **Filtering**: EMA (Exponential Moving Average) smoothing of RGB/HSV values
- **Buffering**: Circular anti-oscillation buffers
- **Coordination**: Selective sending to Pure Data and other modules
- **Intelligence**: Avoids saturation by filtering minor changes

```python
# Configuration
COLOR_BUFFER_SIZE = 5     # Anti-oscillation buffer size
EMA_ALPHA = 0.0005       # Exponential smoothing factor
```

### 🎵 **Pure Data (`main.pd`)**
**Role**: Real-time sound synthesis engine
- **OSC Reception**: HSV messages from `logic.py`
- **Synthesis**: Generative algorithms based on colors
- **Fundamental note**: Pitch calculation from hue (H)
- **Modulation**: Saturation and value control timbre and dynamics
- **Output**: Stereo audio to system DAC

```
# Color → sound mapping
H (hue) → Fundamental note (60-127 MIDI)
S (saturation) → Intensity/timbre
V (value) → Volume/dynamics
```

### 💡 **LED Controller (`led_controller.py`)**
**Role**: Main LED strip management
- **Hardware**: Direct GPIO control via `lib/ledstrip.py`
- **Reception**: Direct RGB messages from `vision.py`
- **Smoothing**: Anti-flicker with buffers and averaging
- **Performance**: Real-time synchronized updates

```python
# GPIO configuration
CLK_PIN = 16  # LED strip clock pin
DAT_PIN = 20  # LED strip data pin
```

### 🤖 **Arduino Serial (`arduino_serial.py`)**
**Role**: Interface with mechanical controller
- **Communication**: USB serial 9600 baud with Arduino
- **RGB Commands**: Color transmission to Arduino LED
- **Monitoring**: Servo and LED status monitoring
- **Robustness**: Automatic reconnection on disconnection

### 🎼 **Music Engine (`music_engine.py`)**
**Role**: Musical extension (skeleton module)
- **Infrastructure**: Ready for advanced musical logic
- **OSC**: Listens to `/event` events 
- **Extensibility**: Base for future musical features

### 🔧 **LED Library (`lib/ledstrip.py`)**
**Role**: Low-level LED strip driver
- **Protocol**: Precise timing implementation (20µs) Arduino-compatible
- **Smoothing**: Circular buffers and color interpolation
- **Performance**: Optimized for high-frequency real-time updates

## System configuration

### Configuration files

#### `network.json` - OSC network configuration
```json
{
  "osc": {
    "router": {"ip": "127.0.0.1", "port": 5005},
    "puredata": {"ip": "127.0.0.1", "port": 9000},
    "logic": {"ip": "127.0.0.1", "port": 9001},
    "led": {"ip": "127.0.0.1", "port": 9002},
    "arduino_serial": {"ip": "127.0.0.1", "port": 9004}
  }
}
```

#### `config.json` - Color processing parameters
```json
{
  "color_processing": {
    "saturation_boost": 1.8,
    "contrast_boost": 1.3,
    "brightness_boost": 0.5
  }
}
```

### Systemd services

The system operates with 7 coordinated services:

- **`vision.service`**: Camera capture and color analysis
- **`osc_router.service`**: Central OSC router (port 5005)
- **`logic.service`**: Color data processing and filtering
- **`puredata.service`**: Pure Data audio engine
- **`led_controller.service`**: Main LED strip control
- **`arduino_serial.service`**: Arduino communication (servo + LED)
- **`music_engine.service`**: Extended music engine (skeleton)

### Hardware
- **Raspberry Pi 5** (central unit with camera processing)
- **Camera module**: Raspberry Pi Camera Module v2 (IMX219)
- **LED ring**: Neopixel ring for visual feedback
- **Arduino Uno**: Controls canvas rotation and LED indicator
  - **Servo motor**: 180° 25kg servo for canvas rotation
  - **WS2812 LED**: Single pixel for status and welcome sequence
- **Canvas support**: Mechanical structure for circular canvases

## Installation and deployment

### Two-tier development architecture
1. **Development machine**: Code modification and testing (Mac/Linux)
2. **Raspberry Pi**: Production execution of the installation

### Initial Raspberry Pi setup (one-time only)

#### 1. System preparation
```bash
# On the Raspberry Pi
curl -O https://raw.githubusercontent.com/basichumantastes/Tourne_Disque_synesthesique/main/tools/deployment/setup_raspberry_complete.sh
chmod +x setup_raspberry_complete.sh
./setup_raspberry_complete.sh
sudo reboot
```

**The installation script configures**:
- System dependencies (OpenCV, PureData, Python, Arduino CLI)
- Raspberry Pi 5 camera module
- Folder structure and systemd services
- Python virtual environment with all dependencies
- Camera and GPIO configuration testing

#### 2. Development setup
```bash
# On the development machine
git clone https://github.com/basichumantastes/Tourne_Disque_synesthesique.git
cd Tourne_Disque_synesthesique

# Create SSH password file
echo "your_raspberry_password" > .ssh_password
chmod 600 .ssh_password

# Modify IP in tools/deployment/deploy.sh if necessary
```

### Continuous deployment (with each update)

#### Python-only deployment (default)
```bash
./tools/deployment/deploy.sh
```

#### Complete deployment with Arduino
```bash
./tools/deployment/deploy.sh --with-arduino
```

**The deployment script**:
- Synchronizes all Python files to the Raspberry Pi
- Updates Python dependencies in virtual environment
- Optionally compiles and uploads Arduino code
- Restarts all systemd services
- Checks service status and displays errors

### Verification and monitoring

#### Service status
```bash
# On the Raspberry Pi
sudo systemctl status vision.service osc_router.service logic.service
sudo systemctl status puredata.service led_controller.service arduino_serial.service
```

#### Real-time logs
```bash
# General logs
sudo journalctl -f

# Service-specific logs
sudo journalctl -u vision.service -f
sudo journalctl -u arduino_serial.service -f

# Quick debug scripts
./check_logs.sh           # Arduino logs
./test_arduino_path.sh    # Arduino file diagnostics
```

#### OSC network monitoring
```bash
# Test OSC message reception (port 9010 = dev)
# Install on development machine:
pip install python-osc

# OSC monitoring script
python3 -c "
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

def print_osc_message(address, *args):
    print(f'OSC: {address} {args}')

dispatcher = Dispatcher()
dispatcher.set_default_handler(print_osc_message)
server = BlockingOSCUDPServer(('0.0.0.0', 9010), dispatcher)
print('Listening OSC on port 9010...')
server.serve_forever()
"
```

## Development and debugging

### Project structure
```
src/
├── raspberry/           # Raspberry Pi code
│   ├── scripts/        # Main Python modules
│   │   ├── vision.py           # Capture and color analysis
│   │   ├── osc_router.py       # Central OSC router
│   │   ├── logic.py            # Color data processing
│   │   ├── led_controller.py   # LED strip control
│   │   ├── arduino_serial.py   # Arduino communication
│   │   └── music_engine.py     # Music engine (skeleton)
│   ├── puredata/       # Pure Data patches
│   │   └── main.pd             # Real-time sound synthesis
│   ├── lib/            # Shared libraries
│   │   └── ledstrip.py         # LED strip driver
│   ├── services/       # Systemd service files
│   └── config/         # JSON configuration files
└── arduino/            # Arduino code (servo + LED)
    └── platformio/
        └── src/
            └── main.ino        # Servo and WS2812 LED control
```

### Included debugging tools

- **`check_logs.sh`**: Quick Arduino log display
- **`test_arduino_path.sh`**: Arduino file structure diagnostics  
- **Service monitoring**: Real-time status during deployment
- **OSC debugging**: Port 9010 for development monitoring

### Modification and testing

#### 1. Local modification
```bash
# Edit code on development machine
vim src/raspberry/scripts/vision.py
```

#### 2. Testing and deployment
```bash
# Quick deployment (Python only)
./tools/deployment/deploy.sh

# Log verification
ssh raspberry_ip "sudo journalctl -u vision.service -n 20"
```

#### 3. Arduino (if necessary)
```bash
# Arduino modification + upload
./tools/deployment/deploy.sh --with-arduino
```

### Configurable parameters

#### Vision and color (`config.json`)
- `saturation_boost`: Saturation amplification (default: 1.8)
- `contrast_boost`: Contrast enhancement (default: 1.3)  
- `brightness_boost`: Brightness adjustment (default: 0.5)

#### Logic processing (`logic.py`)
- `COLOR_BUFFER_SIZE`: Anti-oscillation buffer size (default: 5)
- `EMA_ALPHA`: Exponential smoothing factor (default: 0.0005)

#### Arduino mechanics (`main.ino`)
- `stepInterval`: Servo rotation interval (default: 30000ms)
- `step`: Servo movement precision (default: 10µs)
- `rainbowDuration`: Welcome sequence duration (default: 5000ms)

## Detailed data flow

### Color → sound pipeline
```
Camera → vision.py → osc_router → logic.py → PureData → Audio
  │                      │
  └──────────────────────┴─────→ led_controller.py → LED Strip
```

### Color → Arduino pipeline  
```
vision.py → osc_router → arduino_serial.py → USB serial → Arduino → WS2812 LED
```

### Detailed OSC messages
```
# Vision → Router (10 Hz)
/vision/color/raw/rgb/r [0-255]
/vision/color/raw/rgb/g [0-255] 
/vision/color/raw/rgb/b [0-255]
/vision/color/raw/hsv/h [0-360]
/vision/color/raw/hsv/s [0-255]
/vision/color/raw/hsv/v [0-255]

# Logic → PureData (filtered)
/logic/color/hsv/h [0-360]
/logic/color/hsv/s [0-255]
/logic/color/hsv/v [0-255]

# Arduino → System (feedback)
/arduino/servo/position [500-2350]
/arduino/led/rgb [r,g,b]
```


## License

This project is distributed under the MIT License. See the `LICENSE` file for more details.

### MIT License

Copyright (c) 2025 [Yoann Blanchard](

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
