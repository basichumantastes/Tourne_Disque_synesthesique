# Machine Synesthésique

## Concept
Installation artistique transformant des toiles circulaires en partitions visuelles et sonores. Le dispositif crée une expérience synesthésique où les couleurs se traduisent en lumière et en musique.

## Fonctionnement
1. **Lecture** : Une caméra analyse en temps réel les couleurs d'une toile circulaire en rotation
2. **Translation lumineuse** : Un halo LED reproduit instantanément la couleur perçue
3. **Translation sonore** : Les données chromatiques alimentent un moteur de musique générative (Pure Data)
4. **Synesthésie** : Chaque toile devient une partition unique, créant une expérience multi-sensorielle où couleur, lumière et son se répondent

## Architecture

### Hardware
- Raspberry Pi 5 (unité centrale)
- Camera Module (capture)
- Bandeau LED (retour lumineux)
- Système de rotation de la toile

### Software
- **Vision** : Capture et analyse des couleurs en temps réel
- **Contrôle LED** : Reproduction lumineuse des couleurs détectées
- **Logique** : Coordination des différents modules
- **Musique** : Génération sonore via Pure Data

## Structure du Projet
```
.
├── config/                 # Configuration
├── requirements/           # Dépendances Python
├── src/
│   ├── raspberry/         # Code principal
│   │   ├── lib/          # Bibliothèques partagées
│   │   ├── puredata/     # Patches Pure Data
│   │   ├── scripts/      # Scripts Python
│   │   └── services/     # Services systemd
│   └── arduino/          # Code Arduino (si utilisé)
└── tools/                # Outils de déploiement
```