# Raspberry Sender

Ce Raspberry Pi est responsable de :
- La détection des couleurs via la caméra
- L'envoi des données de couleur via OSC au raspberry_receiver
- Le contrôle du bandeau LED

## Configuration requise

- Raspberry Pi (peut fonctionner en mode headless)
- Python 3 avec les bibliothèques :
  - python-osc
  - opencv-python
  - rpi_ws281x (pour le contrôle LED)

## Installation

1. Installez les dépendances Python :
```bash
pip3 install -r requirements.txt
```

2. Configurez le fichier config.json dans le dossier scripts/ avec :
   - Les paramètres de la caméra
   - L'adresse IP du raspberry_receiver
   - La configuration du bandeau LED

## Utilisation

1. Le script principal est lancé automatiquement via supervisor
2. Les logs sont disponibles dans le dossier configuré dans supervisor.conf
3. Le script ledstrip.py gère le bandeau LED
4. Le script osc_color_sender.py gère la détection et l'envoi des couleurs

## Notes

- La configuration réseau est gérée dans le fichier config/network.json à la racine du projet
- Assurez-vous que la caméra est bien activée dans la configuration du Raspberry Pi