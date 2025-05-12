# Documentation du Système de Routage OSC

## Vue d'ensemble

Le système de routage OSC du "Tourne Disque Synesthésique" utilise une architecture centralisée de type hub-and-spoke. Tous les messages passent par un routeur central qui les distribue de manière ciblée aux modules appropriés selon une table de routage hiérarchique.

```
┌─────────────┐                   ┌──────────────┐                 ┌─────────────┐
│             │  /vision/color/   │              │  /logic/color/  │             │
│  Module A   │ ───────────────►  │ OSC Router   │ ───────────────►│  Module B   │
│ (émetteur)  │                   │ (port 5005)  │                 │ (récepteur) │
│             │                   │              │                 │             │
└─────────────┘                   └──────────────┘                 └─────────────┘
```

## Convention d'adressage

Le système utilise une convention d'adressage standardisée qui inclut toujours le module source :

```
/module_source/type/donnée
```

Par exemple :
- `/vision/color/raw/rgb` : données RGB brutes du module vision
- `/logic/color/rgb` : données RGB traitées par le module logic

Cette convention permet un routage hiérarchique basé sur le préfixe du module source, ce qui simplifie grandement la configuration du système.

## Routage hiérarchique

La table de routage est conçue pour fonctionner de manière hiérarchique avec deux types d'entrées :

1. **Préfixes de module** (se terminant par `/`) : définissent où router tous les messages d'un module
2. **Adresses spécifiques** : permettent de créer des exceptions pour des messages particuliers

```python
self.routes = {
    # Routage par module source
    "/vision/": ["logic", "led"],     # Tous les messages vision vers logic et led
    "/logic/": ["led", "puredata", "music_engine"],  # Messages logic vers LED, PD et music engine
    
    # Cas spécifiques qui remplacent les règles générales
    "/vision/color/raw/hsv": ["logic"],  # HSV uniquement vers logic
}
```

Cette approche hiérarchique simplifie grandement la configuration et la maintenance du système.

## Algorithme de routage

1. Le routeur reçoit un message OSC d'un module source
2. Il recherche d'abord une correspondance exacte dans la table de routage
3. Si aucune correspondance exacte n'est trouvée, il recherche un préfixe correspondant
4. Si aucune règle ne correspond, le message est diffusé à tous les clients (comportement par défaut)

```python
# Extrait simplifié de osc_router.py
def handle_message(self, address, *args):
    # Essayer d'abord une correspondance exacte
    if address in self.routes:
        destinations = self.routes[address]
        # Envoyer aux destinations
        return
        
    # Essayer la correspondance de préfixe
    for prefix, destinations in self.routes.items():
        if prefix.endswith('/') and address.startswith(prefix):
            # Envoyer aux destinations
            return
    
    # Aucune route trouvée, diffuser à tous
    # ...
```

## Déclaration des modules

### Configuration dans network.json

Tous les modules sont déclarés dans le fichier `network.json`. C'est le point de configuration central pour l'ensemble du système :

```json
{
  "osc": {
    "puredata": {
      "ip": "127.0.0.1",
      "port": 9000
    },
    "logic": {
      "ip": "127.0.0.1",
      "port": 9001
    },
    "led": {
      "ip": "127.0.0.1",
      "port": 9002
    },
    "music_engine": {
      "ip": "127.0.0.1",
      "port": 9003
    }
  }
}
```

## Flux de données

### Communication des données de couleur

1. `vision.py` capture les couleurs et envoie :
   - `/vision/color/raw/rgb` (liste groupée) → routé vers logic et led (règle `/vision/`)
   - `/vision/color/raw/hsv` (liste groupée) → routé uniquement vers logic (règle spécifique)
   - `/vision/color/raw/rgb/r`, `/vision/color/raw/rgb/g`, `/vision/color/raw/rgb/b` (valeurs individuelles) → routés vers logic
   - `/vision/color/raw/hsv/h`, `/vision/color/raw/hsv/s`, `/vision/color/raw/hsv/v` (valeurs individuelles) → routés vers logic

2. `logic.py` traite les valeurs avec la moyenne mobile exponentielle (EMA) et envoie :
   - `/logic/color/ema/r`, `/logic/color/ema/g`, `/logic/color/ema/b` (valeurs individuelles RGB) → routés vers puredata uniquement
   - `/logic/color/ema/h`, `/logic/color/ema/s`, `/logic/color/ema/v` (valeurs individuelles HSV) → routés vers puredata uniquement

3. Flux des données :
   - Contrôleur LED : utilise les valeurs RGB brutes du module vision (`/vision/color/raw/rgb`)
   - Pure Data : utilise les valeurs EMA calculées par le module logic (`/logic/color/ema/*`)

## Adresses OSC standardisées

| Adresse OSC | Description | Format de données |
|-------------|-------------|-------------------|
| `/vision/color/raw/rgb` | Couleur RGB brute (groupée) | [r, g, b] (0-255) |
| `/vision/color/raw/rgb/r` | Composante rouge brute | r (0-255) |
| `/vision/color/raw/rgb/g` | Composante verte brute | g (0-255) |
| `/vision/color/raw/rgb/b` | Composante bleue brute | b (0-255) |
| `/vision/color/raw/hsv` | Couleur HSV brute (groupée) | [h, s, v] (h: 0-360, s,v: 0-100) |
| `/vision/color/raw/hsv/h` | Composante teinte brute | h (0-360) |
| `/vision/color/raw/hsv/s` | Composante saturation brute | s (0-100) |
| `/vision/color/raw/hsv/v` | Composante valeur brute | v (0-100) |
| `/logic/color/ema/rgb` | Couleur RGB traitée EMA (groupée) | [r, g, b] (0-255) |
| `/logic/color/ema/r` | Composante rouge traitée EMA | r (0-255) |
| `/logic/color/ema/g` | Composante verte traitée EMA | g (0-255) |
| `/logic/color/ema/b` | Composante bleue traitée EMA | b (0-255) |
| `/logic/color/ema/h` | Teinte traitée EMA | h (0-360) |
| `/logic/color/ema/s` | Composante saturation traitée EMA | s (0-100) |
| `/logic/color/ema/v` | Valeur traitée EMA | v (0-100) |
| `/arduino/motion/speed` | Vitesse de rotation | [speed] (-1.0 à 1.0) |
| `/arduino/motion/direction` | Direction de rotation | [direction] (-1, 0, 1) |
| `/logic/event` | Événement logique | [type, *params] |
| `/music_engine/event` | Événement du moteur musical | [type, *params] |

## Bonnes pratiques

1. **Identification de la source** : Toujours préfixer les adresses OSC avec le nom du module émetteur
2. **Hiérarchie cohérente** : Organiser les adresses en niveaux logiques : `/source/catégorie/sous-catégorie/donnée`
3. **Utiliser les surcharges avec parcimonie** : N'utiliser des règles spécifiques que lorsque c'est vraiment nécessaire
4. **Documenter les préfixes** : S'assurer que chaque préfixe est documenté avec sa destination
5. **Configuration centralisée** : Toutes les adresses et ports sont définis dans `network.json`

## Avantages du routage hiérarchique

- **Simplicité** : Configuration plus concise et plus facile à comprendre
- **Maintenabilité** : L'ajout de nouveaux types de messages ne nécessite pas de modifier la table de routage
- **Flexibilité** : Possibilité de créer des exceptions pour des cas spécifiques
- **Extensibilité** : Facilite l'ajout de nouveaux modules au système

## Débogage

En cas de problèmes :
- Observer les logs du routeur qui affichent le mode de routage utilisé pour chaque message
- Vérifier si un message utilise une correspondance exacte, un préfixe ou le comportement par défaut
- Examiner les messages diffusés à tous (qui n'ont pas trouvé de route correspondante)

## Comment implémenter cette approche dans un nouveau module

Pour qu'un module communique avec ce système de routage, il doit :

1. **Être défini** dans le fichier `network.json` avec son adresse IP et son port
2. **Préfixer ses messages** avec son identifiant (par exemple, `/mon_module/action/données`)
3. **Écouter** sur son propre port pour recevoir les messages qui lui sont destinés
4. **Être ajouté** à la table de routage du routeur OSC avec un préfixe (par exemple, `/mon_module/: ["destinataire1", "destinataire2"]`)

Voici un exemple d'implémentation pour un module générique :

```python
#!/usr/bin/env python3
from pythonosc import udp_client, dispatcher, osc_server
import json
import os
import threading

def load_network_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    config_path = os.path.join(parent_dir, "network.json")
    
    with open(config_path, "r") as file:
        return json.load(file)

class MyModule:
    def __init__(self, module_name="my_module"):
        # Chargement de la configuration réseau
        config = load_network_config()
        self.module_name = module_name
        
        # Vérifier que le module est configuré dans network.json
        if module_name not in config['osc']:
            raise ValueError(f"Module {module_name} non configuré dans network.json")
            
        # Obtenir la configuration du module
        module_config = config['osc'][module_name]
        self.local_ip = module_config['ip']
        self.local_port = module_config['port']
        
        # Client pour envoyer des messages au routeur
        self.client = udp_client.SimpleUDPClient("127.0.0.1", 5005)
        
        # Dispatcher pour recevoir des messages
        self.dispatcher = dispatcher.Dispatcher()
        self.setup_handlers()
        
        # Serveur OSC pour écouter les messages
        self.server = osc_server.ThreadingOSCUDPServer(
            (self.local_ip, self.local_port), self.dispatcher)
    
    def setup_handlers(self):
        """Configurer les gestionnaires pour les messages entrants"""
        # Pour un module générique, nous pouvons configurer des gestionnaires pour tous
        # les messages possibles que le module peut recevoir de n'importe quelle source
        self.dispatcher.set_default_handler(self.handle_all_messages)
        
    def handle_all_messages(self, address, *args):
        print(f"Message reçu : {address} {args}")
        
        # Extraction optionnelle du module source pour un traitement différencié
        parts = address.split('/')
        if len(parts) > 1:
            source_module = parts[1]
            print(f"  ↳ Source : {source_module}")
        
    def send_message(self, type_msg, *args):
        """Envoyer un message OSC avec préfixe du module source"""
        address = f"/{self.module_name}/{type_msg}"
        self.client.send_message(address, args)
        
    def run(self):
        print(f"Module {self.module_name} démarré sur {self.local_ip}:{self.local_port}")
        self.server.serve_forever()

# Exemple d'utilisation
if __name__ == "__main__":
    module = MyModule("my_module")
    module.send_message("status/active", True)  # Envoie /my_module/status/active
    module.run()
```

*Documentation mise à jour le 12 mai 2025*