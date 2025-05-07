# Synesthetic Machine - Open Source Project

## Concept
Open source artistic installation transforming circular canvases into visual and sound scores. The device creates a synesthetic experience where colors translate into light and music.

## How it works
1. **Reading**: A camera analyzes the colors of a rotating circular canvas in real time
2. **Light translation**: An LED halo instantly reproduces the perceived color
3. **Sound translation**: The chromatic data feeds a generative music engine (Pure Data)
4. **Synesthesia**: Each canvas becomes a unique score, creating a multi-sensory experience where color, light, and sound respond to each other

## Architecture

### Hardware
- Raspberry Pi 5 (central unit)
- Camera module: Raspberry Pi Camera Module v2
- LED ring: Neopixel ring

## Installation and Deployment

The project uses a two-tier development architecture:
1. **Development machine**: Where you modify and test the code
2. **Raspberry Pi**: Where the project runs in production

### Initial Raspberry Pi Setup (one-time only)

Before you can deploy the code, you need to set up the Raspberry Pi:

1. **Prepare your Raspberry Pi**:
   - Install Raspberry Pi OS (64-bit)
   - Configure SSH and Wi-Fi network
   - Note the Raspberry Pi's IP address

2. **Transfer the installation script**:
   ```bash
   # From your development machine
   scp ./tools/deployment/setup_raspberry_complete.sh blanchard@<RASPBERRY_PI_IP>:~/
   ```

3. **Run the installation script on the Raspberry Pi**:
   ```bash
   # On the Raspberry Pi via SSH
   chmod +x ~/setup_raspberry_complete.sh
   ./setup_raspberry_complete.sh
   ```

4. **Restart the Raspberry Pi if necessary**:
   ```bash
   sudo reboot
   ```

The `setup_raspberry_complete.sh` script performs the following operations:
- Updates the system and installs required dependencies
- Configures the camera for Raspberry Pi 5
- Prepares the folder structure
- Configures systemd services
- Creates a Python virtual environment
- Tests the camera configuration

### Continuous Deployment (with each update)

To deploy code updates to the Raspberry Pi:

1. **Create a password file**:
   - Create a `.ssh_password` file at the root of the project
   - Put your SSH password for the Raspberry Pi in it
   - Protect this file with `chmod 600 .ssh_password`

2. **Modify deployment parameters** (if necessary):
   - Open `tools/deployment/deploy.sh`
   - Modify `REMOTE_USER` and `REMOTE_HOST` according to your configuration

3. **Launch the deployment**:
   ```bash
   # From the project root on your development machine
   ./tools/deployment/deploy.sh
   ```

The deployment script:
- Synchronizes project files with the Raspberry Pi
- Updates Python dependencies
- Configures and restarts systemd services
- Checks the status of services

### Service Structure

The project is divided into several systemd services that work together:
- `vision.service`: Color analysis via camera
- `led_controller.service`: LED ring control
- `osc_router.service`: Communication between components
- `logic.service`: Main application logic
- `music_engine.service`: Sound generation
- `puredata.service`: Audio engine

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
