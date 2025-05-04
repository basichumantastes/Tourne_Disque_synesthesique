# Tourne Disque Synesthésique

Installation artistique combinant un Raspberry Pi et un Arduino pour créer une expérience synesthésique interactive.

## Structure du Projet

```
📁 TOURNE_DISQUE_SYNESTHESIQUE/
├── src/
│   ├── raspberry/           # Code Python pour le Raspberry Pi
│   │   ├── scripts/
│   │   │   ├── osc_color_sender.py  # Script principal de détection et envoi OSC
│   │   │   ├── ledstrip.py          # Gestion du ruban LED
│   │   │   └── config.json          # Configuration du projet
│   │   └── supervisor.conf  # Configuration du démon supervisor
│   └── arduino/            # Code Arduino/PlatformIO
│       └── platformio/     # Configuration PlatformIO
├── tools/
│   └── deployment/         # Outils de déploiement
│       ├── deploy.sh       # Script de déploiement vers le Raspberry Pi
│       └── setup_raspberry.sh  # Configuration initiale du Raspberry Pi
├── requirements/           # Dépendances Python
└── docs/                  # Documentation
```

## Prérequis

- Python 3.x sur la machine de développement et le Raspberry Pi
- PlatformIO Core (pour le développement Arduino)
- Git
- Accès SSH au Raspberry Pi (IP: 192.168.0.104, user: blanchard)
- VS Code recommandé comme éditeur

## Configuration du Développement

1. Cloner le dépôt :
   ```bash
   git clone [URL_DU_REPO] TOURNE_DISQUE_SYNESTHESIQUE
   cd TOURNE_DISQUE_SYNESTHESIQUE
   ```

2. Configurer l'environnement Python :
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Sur Unix/MacOS
   pip install -r requirements/dev-requirements.txt
   ```

3. Configurer PlatformIO (pour Arduino) :
   ```bash
   cd src/arduino/platformio
   pio project init
   ```

## Développement

### Workflow

1. **Développement Local** :
   - Tout le développement se fait dans le dossier `src/`
   - Les scripts Python sont dans `src/raspberry/scripts/`
   - La configuration est dans `src/raspberry/scripts/config.json`

2. **Test des Modifications** :
   - Testez localement autant que possible
   - Pour les tests nécessitant le hardware, utilisez le déploiement rapide

### Configuration du Projet

Le fichier `src/raspberry/scripts/config.json` contient les paramètres principaux :
```json
{
    "osc_ip": "192.168.0.118",
    "osc_port": 12000,
    "rotation_speed": 200,
    "h_ratio": 1.0,
    "s_ratio": 1.0,
    "v_ratio": 1.0
}
```

## Déploiement

### Installation Initiale sur un Nouveau Raspberry Pi

1. Exécuter le script d'installation :
   ```bash
   ./tools/deployment/setup_raspberry.sh
   ```
   Ce script :
   - Met à jour le système
   - Installe les dépendances nécessaires
   - Configure l'environnement Python
   - Configure supervisor
   - Crée les dossiers de logs

2. Vérifier l'installation :
   ```bash
   ssh blanchard@192.168.0.104
   sudo supervisorctl status tourne_disque
   ```

### Déploiements Réguliers

Pour déployer vos modifications :
```bash
./tools/deployment/deploy.sh
```

Le script synchronise uniquement les fichiers modifiés et redémarre le service si nécessaire.

## Maintenance et Logs

### Gestion des Processus

Le projet utilise supervisor pour gérer le processus Python en mode headless :
- Les logs sont dans `/home/blanchard/color_detection_project/logs/`
- Le service peut être contrôlé avec :
  ```bash
  sudo supervisorctl status tourne_disque
  sudo supervisorctl restart tourne_disque
  ```

### Logs
Les logs sont stockés dans :
- `/home/blanchard/color_detection_project/logs/supervisor.err.log` pour les erreurs
- `/home/blanchard/color_detection_project/logs/supervisor.out.log` pour la sortie standard
- `/home/blanchard/color_detection_project/logs/supervisord.log` pour les logs de supervisor

Pour voir les logs en temps réel :
```bash
tail -f /home/blanchard/color_detection_project/logs/supervisor.out.log
```

## Licence

[À définir]