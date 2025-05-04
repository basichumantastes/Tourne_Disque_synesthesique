# Raspberry Receiver

Ce Raspberry Pi est responsable de :
- La réception des données OSC envoyées par le raspberry_sender
- L'exécution du patch Pure Data qui traite ces données

## Configuration requise

- Raspberry Pi (avec interface graphique)
- Pure Data installé
- Python avec python-osc pour le relais OSC si nécessaire

## Installation

1. Installez Pure Data :
```bash
sudo apt-get update
sudo apt-get install puredata
```

2. Placez le patch Pure Data dans le dossier `puredata/`

## Utilisation

1. Démarrez Pure Data
2. Ouvrez le patch principal dans le dossier `puredata/`
3. Assurez-vous que le port OSC configuré dans Pure Data correspond au port d'envoi du raspberry_sender

## Notes

- Ce Raspberry n'est pas configuré en mode headless car il nécessite une interface graphique pour Pure Data
- La configuration OSC doit correspondre à celle du raspberry_sender (IP et port)