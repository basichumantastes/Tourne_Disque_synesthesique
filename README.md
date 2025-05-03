# Tourne Disque Synesthésique

Installation artistique combinant un Raspberry Pi et un Arduino pour créer une expérience synesthésique interactive.

## Structure du Projet

```
.
├── src/
│   ├── raspberry/        # Code Python pour Raspberry Pi
│   │   └── scripts/     # Scripts Python principaux
│   └── arduino/         # Code Arduino/PlatformIO
│       └── platformio/  # Configuration PlatformIO
├── requirements/        # Dépendances Python et autres
├── tools/
│   └── deployment/     # Scripts de déploiement
└── docs/              # Documentation du projet
```

## Prérequis

- Python 3.x sur la machine de développement et le Raspberry Pi
- PlatformIO Core (pour le développement Arduino)
- Git
- Accès SSH au Raspberry Pi

## Configuration du Développement

1. Cloner le dépôt :
   ```bash
   git clone [URL_DU_REPO]
   ```

2. Configurer l'environnement Python :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Unix/MacOS
   pip install -r requirements/dev-requirements.txt
   ```

3. Configurer PlatformIO (pour Arduino) :
   ```bash
   cd src/arduino/platformio
   pio project init
   ```

## Déploiement

Le déploiement vers le Raspberry Pi se fait via le script `tools/deployment/deploy.sh` :

```bash
./tools/deployment/deploy.sh [IP_RASPBERRY_PI]
```

## Développement

- Tout le développement se fait en local
- Les tests peuvent être effectués localement
- Le déploiement vers le Raspberry Pi se fait via rsync
- Le code Arduino est géré via PlatformIO pour une meilleure portabilité

## Licence

[À définir]