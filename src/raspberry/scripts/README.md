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
- Réception directe des données couleur brutes via OSC (/color/raw/rgb)
- Réception des données couleur traitées (si nécessaire) via OSC (/color/rgb)
- Pilotage du bandeau LED via GPIO

## logic.py
Coordination entre la détection des couleurs et les sorties (principalement Pure Data).

### Fonctionnalités
- Réception des données RGB/HSV depuis vision.py
- Distribution des données HSV vers Pure Data

## osc_router.py
Routeur central pour la communication OSC entre les différents composants.

### Fonctionnalités
- Écoute sur le port 5005
- Redistribution des messages vers tous les destinataires configurés
- Point central pour toute la communication inter-modules

## Communication OSC

### Architecture réseau
Toutes les communications passent par le routeur OSC central :

```
 ┌──────────┐         ┌─────────────────┐
 │          │ ----→   │                 │
 │ vision.py│  OSC    │  osc_router.py  │
 │          │ ----→   │    (port 5005)  │
 └──────────┘         │                 │
                      └─────┬─────┬─────┘
                            │     │
                            │     │
                            │     └───────────────┐
                            │                     │
                            ↓                     ↓
                      ┌───────────┐         ┌──────────┐
                      │           │         │          │
                      │ logic.py  │         │led_ctrl.py│
                      │           │         │          │
                      └─────┬─────┘         └──────────┘
                            │
                            ↓
                      ┌───────────┐
                      │           │
                      │ PureData  │
                      │           │
                      └───────────┘
```

### Flux de données par type de message
- Données couleur brutes : `vision.py → osc_router.py → led_controller.py` (flux direct)
- Données HSV pour l'audio : `vision.py → osc_router.py → logic.py → PureData`
- Tous les messages transitent par le routeur OSC central

