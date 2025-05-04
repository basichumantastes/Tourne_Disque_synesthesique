# Arduino

Ce module Arduino est utilisé pour :
- La gestion des moteurs du tourne-disque
- La communication avec les capteurs de position
- Le contrôle de la vitesse de rotation

## Configuration requise

- Arduino (compatible avec PlatformIO)
- Environnement PlatformIO configuré
- Moteurs pas à pas et leurs drivers
- Capteurs de position

## Installation

1. Ouvrez le projet dans PlatformIO
2. Vérifiez la configuration dans platformio.ini
3. Compilez et téléversez le code vers l'Arduino

## Configuration

Le fichier platformio.ini dans le dossier platformio/ contient :
- La configuration du microcontrôleur
- Les dépendances du projet
- Les paramètres de compilation

## Notes

- Assurez-vous que les broches utilisées correspondent à votre câblage physique
- Vérifiez la compatibilité des bibliothèques avec votre modèle d'Arduino
- La vitesse des moteurs peut être ajustée dans le code source