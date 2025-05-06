# Configuration Raspberry Pi

## Installation

### Dépendances système
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-opencv \
    puredata \
    python3-pip \
    python3-venv
```

### Configuration Hardware

#### Camera
- Activer la caméra dans `raspi-config`
- Distance : ajustée pour cadrer la zone de détection

#### LED
- Connexion du bandeau LED via GPIO

### Installation du projet
1. Cloner le repository
2. Installer les dépendances Python
3. Installer les services systemd

## Services
- vision.service : Capture et analyse vidéo
- logic.service : Coordination et OSC
- puredata.service : Génération musicale

## Dépannage

### Camera
- Vérifier que la caméra est activée : `vcgencmd get_camera`
- Tester la capture : `raspistill -o test.jpg`

### Services
- Vérifier l'état : `systemctl status <service>`
- Logs détaillés : `journalctl -u <service> -n 50`