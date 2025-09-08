# Arduino - Servo and LED Controller

This Arduino module controls:
- **180° Servo (25kg)**: Automatic rotation of circular canvases
- **WS2812 LED**: Visual indication and welcome sequence
- **Serial communication**: Receives color commands from Raspberry Pi

## Features

### Servo Motor
- Automatic oscillation between 500µs and 2350µs (PWM)
- Movement every 30 seconds with 10µs steps
- Precise control for smooth canvas rotation

### WS2812 LED (1 pixel)
- **Welcome sequence**: 5-second rainbow animation on startup
- **Normal mode**: Displays colors detected by vision system
- Adjustable brightness (default: 100/255)

### Serial Communication
Supports multiple color command formats:
```
rgb,255,128,64    # CSV format
r255g128b064      # Compact format
r255              # Individual components
g128              # (applied when R,G,B complete)
b064
```

## Hardware configuration

### Connections
- **Servo**: Pin 9 (PWM signal)
- **LED**: Pin 6 (WS2812 data)
- **Power**: External 5V supply for servo and LED
- **Communication**: USB serial (9600 baud)

### Specifications
- Servo: 180° 25kg, PWM 500-2500µs
- LED: WS2812 RGB, GRB protocol
- Timing: 30 seconds between servo movements

## Installation and Upload

### Via deployment script (recommended)
```bash
# From development machine
./tools/deployment/deploy.sh --with-arduino
```

### Manual upload
```bash
# On Raspberry Pi
cd /home/blanchard/tourne_disque/src/arduino/platformio
arduino-cli compile --fqbn arduino:avr:uno src/
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno src/
```

## Dependencies

- **FastLED**: WS2812 LED control
- **Servo**: Servo control (Arduino standard library)

## Monitoring

### Serial messages (debug disabled)
Code has been optimized without serial debug for better performance.

### Status verification
```bash
# Arduino service logs on Raspberry Pi
sudo journalctl -u arduino_serial.service -n 50
```

## Configurable parameters

In `main.ino`:
```cpp
const unsigned long stepInterval = 30000;    // Servo interval (ms)
const int step = 10;                         // Servo step (µs)
const unsigned long rainbowDuration = 5000;  // Rainbow duration (ms)
const int minPulse = 500;                    // PWM min (µs)
const int maxPulse = 2350;                   // PWM max (µs)
```