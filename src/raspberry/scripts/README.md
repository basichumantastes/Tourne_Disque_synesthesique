# Scripts Python

## vision.py
Script de capture et d'analyse vidéo en temps réel.

### Fonctionnalités
- Capture vidéo via libcamera (Raspberry Pi)
- Détection des couleurs dominantes via OpenCV
- Envoi des données RGB et HSV via OSC

## led_controller.py
Contrôle du bandeau LED en fonction des couleurs détectées.

### Fonctionnalités
- Réception des données couleur via OSC
- Pilotage du bandeau LED via GPIO
- Transitions douces entre les couleurs

## logic.py
Coordination entre la détection des couleurs et les sorties (LED et Pure Data).

### Fonctionnalités
- Réception des données RGB/HSV depuis vision.py
- Lissage des couleurs
- Distribution vers LED et Pure Data

## Communication OSC

### Flux de données
```
vision.py --> logic.py --> led_controller.py
                      --> Pure Data
```

## Utilisation

### Développement
```bash
# Test vision seule
python vision.py

# Test LED seul
python led_controller.py

# Test complet
python vision.py & python logic.py & python led_controller.py
```