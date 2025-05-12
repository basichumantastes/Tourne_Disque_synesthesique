# Synesthetic Machine - Documentation Technique

## Introduction Technique

Le Tourne Disque Synesthésique est une installation interactive basée sur un système distribué qui capture, analyse et transforme des informations chromatiques en temps réel. Cette documentation se concentre sur l'architecture technique et fonctionnelle du projet.

> Pour une exploration détaillée du concept artistique et de l'expérience synesthésique, veuillez consulter [artistic_concept.md](./artistic_concept.md).

## Architecture Technique

### Vue d'ensemble

Le système est basé sur une architecture modulaire distribuée, communiquant principalement via le protocole OSC (Open Sound Control). Cette approche permet une grande flexibilité et une séparation claire des responsabilités entre les différents composants.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │
│   Vision    │───►│   Logic     │───►│     LED     │
│  (Camera)   │    │ (Processing)│    │  (Display)  │
│             │    │             │    │             │
└─────────────┘    └──────┬──────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │             │
                   │  Pure Data  │
                   │   (Audio)   │
                   │             │
                   └─────────────┘
```

### Composants Matériels

- **Raspberry Pi 5**: Unité centrale hébergeant les services principaux
- **Module Caméra**: Capture en temps réel des toiles en rotation
- **Bande LED**: Reproduit sous forme lumineuse les couleurs analysées
- **Système Audio**: Diffuse la composition sonore générée
- **Mécanisme de Rotation**: Permet la rotation constante des toiles circulaires

### Composants Logiciels

Le système est constitué de plusieurs modules indépendants, chacun ayant une responsabilité spécifique:

#### 1. Module Vision (`vision.py`)
- Capture d'image via la caméra
- Analyse des couleurs en temps réel
- Extraction des valeurs RGB et HSV
- Transmission des données chromatiques via OSC

#### 2. Module Logic (`logic.py`)
- Coordination centrale du système
- Réception et traitement des données couleur
- Techniques de lissage (tampons circulaires, moyenne mobile exponentielle)
- Routage des informations vers les autres modules

#### 3. Module LED (`led_controller.py`)
- Contrôle de la bande LED
- Reproduction fidèle des couleurs analysées
- Gestion des transitions et effets lumineux

#### 4. Module Audio (Pure Data)
- Génération algorithmique du son
- Mappage des valeurs RGB/HSV aux paramètres musicaux
- Création d'une atmosphère sonore correspondant aux couleurs

### Flux de Données

1. La caméra capture l'image de la toile en rotation
2. Les données de couleur sont extraites et envoyées au module logic
3. Le module logic applique des algorithmes de lissage pour stabiliser les transitions
4. Les valeurs stabilisées sont envoyées simultanément vers:
   - Le contrôleur LED pour la reproduction lumineuse
   - Pure Data pour la génération sonore

## Détails Techniques

### Protocole de Communication

L'ensemble du système utilise OSC (Open Sound Control) pour la communication entre les composants. Les différents services communiquent via UDP sur des ports spécifiques définis dans le fichier `network.json`.

> Pour une documentation détaillée du système de routage OSC, consultez [osc_routing.md](./osc_routing.md).

### Traitement des Couleurs

Le système utilise plusieurs techniques pour assurer une expérience fluide et stable:

- **Tampons Circulaires**: Stockage temporaire des N dernières valeurs RGB
- **Moyenne Mobile Exponentielle (EMA)**: Algorithme de lissage avec un facteur alpha très bas (0,0005) pour des transitions ultra-douces
- **Double Représentation Chromatique**: Utilisation simultanée des espaces colorimétriques RGB et HSV pour enrichir les possibilités expressives

### Services Systemd

L'installation fonctionne comme un ensemble de services systemd sur le Raspberry Pi, assurant:
- Démarrage automatique au boot
- Redémarrage en cas de crash
- Gestion des dépendances entre services

## Déploiement et Maintenance

### Installation

Le déploiement est automatisé via des scripts situés dans le dossier `tools/deployment/`:
- `setup_raspberry_complete.sh`: Configuration initiale du Raspberry Pi
- `deploy.sh`: Déploiement des mises à jour de code

### Dépendances

Les dépendances du projet sont gérées via pip et documentées dans les fichiers requirements:
- `src/raspberry/requirements.txt`: Dépendances principales pour le Raspberry Pi
- `requirements/mac-requirements.txt`: Dépendances spécifiques pour macOS (développement)


*Documentation mise à jour le 12 mai 2025*