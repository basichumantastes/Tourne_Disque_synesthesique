# Machine Synesthésique - Documentation Contextuelle

## Présentation du Projet

La Machine Synesthésique est une installation artistique interactive qui transforme des toiles circulaires en partitions visuelles et sonores. Cette œuvre crée un pont entre différentes modalités sensorielles (vision, ouïe), incarnant le phénomène neurologique de synesthésie où un stimulus sensoriel déclenche automatiquement une expérience dans une autre modalité sensorielle.

## Concept Artistique

L'installation permet de "voir le son" et d'"entendre les couleurs". Chaque toile circulaire devient une partition unique qui, lorsqu'elle est placée sur le dispositif et mise en rotation, génère simultanément :
- Une réponse lumineuse qui reflète les couleurs de la toile
- Une composition musicale générée algorithmiquement en fonction des données chromatiques

La frontière entre arts visuels et musique s'efface pour créer une expérience multi-sensorielle immersive où les sens se répondent et s'amplifient mutuellement.

## Architecture Technique

### Vue d'ensemble

Le système repose sur une architecture modulaire distribuée, communiquant principalement via le protocole OSC (Open Sound Control). Cette approche permet une grande flexibilité et une séparation claire des responsabilités entre les différents composants.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │
│   Vision    │───►│   Logique   │───►│     LED     │
│  (Caméra)   │    │(Traitement) │    │ (Affichage) │
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

### Composants Hardware

- **Raspberry Pi 5** : Unité centrale qui héberge les services principaux
- **Module Caméra** : Capture en temps réel des toiles en rotation
- **Bandeau LED** : Reproduit les couleurs analysées sous forme lumineuse
- **Système audio** : Restitue la composition sonore générée
- **Mécanisme de rotation** : Permet la rotation constante des toiles circulaires

### Composants Software

Le système est constitué de plusieurs modules indépendants, chacun ayant une responsabilité spécifique :

#### 1. Module Vision (`vision.py`)
- Capture d'images via la caméra
- Analyse des couleurs en temps réel
- Extraction des valeurs RGB et HSV
- Transmission des données chromatiques via OSC

#### 2. Module Logique (`logic.py`)
- Coordination centrale du système
- Réception et traitement des données couleur
- Techniques de lissage (buffers circulaires, moyenne mobile exponentielle)
- Routage des informations vers les autres modules

#### 3. Module LED (`led_controller.py`)
- Contrôle du bandeau LED
- Reproduction fidèle des couleurs analysées
- Gestion des transitions et effets lumineux

#### 4. Module Audio (Pure Data)
- Génération sonore algorithmique
- Mapping des valeurs RGB/HSV vers des paramètres musicaux
- Création d'une ambiance sonore correspondant aux couleurs

### Flux de Données

1. La caméra capture l'image de la toile en rotation
2. Les données de couleur sont extraites et envoyées au module logique
3. Le module logique applique des algorithmes de lissage pour stabiliser les transitions
4. Les valeurs stabilisées sont envoyées simultanément :
   - Au contrôleur LED pour la reproduction lumineuse
   - À Pure Data pour la génération sonore

## Détails Techniques

### Protocole de Communication

L'ensemble du système utilise OSC (Open Sound Control) pour la communication entre composants. Les différents services communiquent via UDP sur des ports spécifiques définis dans le fichier `network.json`.

### Traitement des Couleurs

Le système utilise plusieurs techniques pour garantir une expérience fluide et stable :

- **Buffers circulaires** : Stockage temporaire des N dernières valeurs RGB
- **Moyenne mobile exponentielle (EMA)** : Algorithme de lissage avec un facteur alpha très faible (0.0005) pour des transitions ultra-douces
- **Double représentation colorimétrique** : Utilisation simultanée des espaces RGB et HSV pour enrichir les possibilités expressives

### Services Systemd

L'installation fonctionne comme un ensemble de services systemd sur le Raspberry Pi, garantissant :
- Démarrage automatique au boot
- Redémarrage en cas de crash
- Gestion des dépendances entre services

## Déploiement et Maintenance

### Installation

Le déploiement est automatisé via des scripts situés dans le dossier `tools/deployment/` :
- `setup_raspberry.sh` : Configuration initiale du Raspberry Pi
- `deploy.sh` : Déploiement des mises à jour du code

### Dépendances

Les dépendances du projet sont gérées via pip et documentées dans différents fichiers requirements :
- `requirements.txt` : Dépendances principales pour le Raspberry Pi
- `dev-requirements.txt` : Dépendances additionnelles pour le développement
- `mac-requirements.txt` : Dépendances spécifiques pour macOS (développement)

## Évolutions Possibles

- Développement d'une interface web de contrôle et visualisation
- Intégration de techniques d'intelligence artificielle pour l'analyse des motifs
- Ajout de nouveaux mappings couleur-son plus complexes
- Création d'un mode "collectif" permettant de combiner plusieurs toiles

---

*Documentation créée le 6 mai 2025*