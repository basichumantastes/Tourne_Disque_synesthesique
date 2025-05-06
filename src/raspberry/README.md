# Raspberry Pi Application

Ce Raspberry Pi 5 est responsable de :
- La détection des couleurs via la caméra (vision.py)
- Le traitement et la logique de l'application (logic.py)
- La synthèse sonore via Pure Data (headless)
- Le contrôle du bandeau LED

## Configuration requise

- Raspberry Pi 5
- Python 3 avec les bibliothèques :
  - opencv-python (vision)
  - rpi_ws281x (contrôle LED)
  - python-osc (communication interne)
- Pure Data (mode headless)

## Structure des scripts

- `scripts/vision.py` : Capture et analyse des couleurs
- `scripts/logic.py` : Logique de l'application et coordination
- `scripts/ledstrip.py` : Contrôle du bandeau LED
- `puredata/main.pd` : Patch Pure Data pour la synthèse sonore

## Installation

1. Installez les dépendances système :
```bash
sudo apt update
sudo apt install -y puredata python3-opencv python3-pip
```

2. Installez les dépendances Python :
```bash
pip3 install -r requirements.txt
```

3. Configurez les services systemd :
   - vision.service : Service de détection des couleurs
   - logic.service : Service de logique applicative
   - puredata.service : Service Pure Data headless

## Configuration

- `config.json` : Configuration générale de l'application
- `services/` : Fichiers de configuration des services systemd

## Notes

- Assurez-vous que la caméra est activée dans la configuration du Raspberry Pi
- Les services communiquent en interne via OSC sur localhost
- Pure Data fonctionne en mode headless pour la performance