# OSC Routing System Documentation

## Overview

The OSC routing system of the "Synesthetic Turntable" uses a centralized hub-and-spoke architecture. All messages pass through a central router that distributes them in a targeted way to the appropriate modules according to a hierarchical routing table.

```
┌─────────────┐                   ┌──────────────┐                 ┌─────────────┐
│             │  /vision/color/   │              │  /logic/color/  │             │
│  Module A   │ ───────────────►  │ OSC Router   │ ───────────────►│  Module B   │
│ (sender)    │                   │ (port 5005)  │                 │ (receiver)  │
│             │                   │              │                 │             │
└─────────────┘                   └──────────────┘                 └─────────────┘
```

## Addressing Convention

The system uses a standardized addressing convention that always includes the source module:

```
/source_module/type/data
```

For example:
- `/vision/color/raw/rgb`: raw RGB data from the vision module
- `/logic/color/rgb`: processed RGB data from the logic module

This convention allows hierarchical routing based on the source module prefix, which greatly simplifies the system configuration.

## Hierarchical Routing

The routing table is designed to work hierarchically with two types of entries:

1. **Module prefixes** (ending with `/`): define where to route all messages from a module
2. **Specific addresses**: allow creating exceptions for particular messages

```python
self.routes = {
    # Routing by source module
    "/vision/": ["logic", "led"],     # All vision messages to logic and led
    "/logic/": ["led", "puredata", "music_engine"],  # Logic messages to LED, PD and music engine
    
    # Specific cases that override general rules
    "/vision/color/raw/hsv": ["logic"],  # HSV only to logic
}
```

This hierarchical approach greatly simplifies the configuration and maintenance of the system.

## Routing Algorithm

1. The router receives an OSC message from a source module
2. It first looks for an exact match in the routing table
3. If no exact match is found, it searches for a matching prefix
4. If no rule matches, the message is broadcast to all clients (default behavior)

```python
# Simplified excerpt from osc_router.py
def handle_message(self, address, *args):
    # Try exact match first
    if address in self.routes:
        destinations = self.routes[address]
        # Send to destinations
        return
        
    # Try prefix matching
    for prefix, destinations in self.routes.items():
        if prefix.endswith('/') and address.startswith(prefix):
            # Send to destinations
            return
    
    # No route found, broadcast to all
    # ...
```

## Module Declaration

### Configuration in network.json

All modules are declared in the `network.json` file. This is the central configuration point for the entire system:

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

## Data Flow

### Color Data Communication

1. `vision.py` captures colors and sends:
   - `/vision/color/raw/rgb` (liste groupée) → routed to logic and led (rule `/vision/`)
   - `/vision/color/raw/hsv` (liste groupée) → routed only to logic (specific rule)
   - `/vision/color/raw/rgb/r`, `/vision/color/raw/rgb/g`, `/vision/color/raw/rgb/b` (valeurs individuelles) → routed to logic
   - `/vision/color/raw/hsv/h`, `/vision/color/raw/hsv/s`, `/vision/color/raw/hsv/v` (valeurs individuelles) → routed to logic

2. `logic.py` processes the values with Exponential Moving Average (EMA) and sends:
   - `/logic/color/ema/r`, `/logic/color/ema/g`, `/logic/color/ema/b` (valeurs individuelles RGB) → routed to puredata only
   - `/logic/color/ema/h`, `/logic/color/ema/s`, `/logic/color/ema/v` (valeurs individuelles HSV) → routed to puredata only

3. Flux des données:
   - Contrôleur LED: utilise les valeurs RGB brutes du module vision (`/vision/color/raw/rgb`)
   - Pure Data: utilise les valeurs EMA calculées par le module logic (`/logic/color/ema/*`)

## Standardized OSC Addresses

| OSC Address | Description | Data Format |
|-------------|-------------|-------------------|
| `/vision/color/raw/rgb` | Raw RGB color (grouped) | [r, g, b] (0-255) |
| `/vision/color/raw/rgb/r` | Raw red component | r (0-255) |
| `/vision/color/raw/rgb/g` | Raw green component | g (0-255) |
| `/vision/color/raw/rgb/b` | Raw blue component | b (0-255) |
| `/vision/color/raw/hsv` | Raw HSV color (grouped) | [h, s, v] (h: 0-360, s,v: 0-100) |
| `/vision/color/raw/hsv/h` | Raw hue component | h (0-360) |
| `/vision/color/raw/hsv/s` | Raw saturation component | s (0-100) |
| `/vision/color/raw/hsv/v` | Raw value component | v (0-100) |
| `/logic/color/ema/rgb` | EMA-processed RGB color (grouped) | [r, g, b] (0-255) |
| `/logic/color/ema/r` | EMA-processed red component | r (0-255) |
| `/logic/color/ema/g` | EMA-processed green component | g (0-255) |
| `/logic/color/ema/b` | EMA-processed blue component | b (0-255) |
| `/logic/color/ema/h` | EMA-processed hue | h (0-360) |
| `/logic/color/ema/s` | EMA-processed saturation component | s (0-100) |
| `/logic/color/ema/v` | EMA-processed value | v (0-100) |
| `/arduino/motion/speed` | Rotation speed | [speed] (-1.0 to 1.0) |
| `/arduino/motion/direction` | Rotation direction | [direction] (-1, 0, 1) |
| `/logic/event` | Logic event | [type, *params] |
| `/music_engine/event` | Music engine event | [type, *params] |

## Best Practices

1. **Source identification**: Always prefix OSC addresses with the name of the sending module
2. **Consistent hierarchy**: Organize addresses in logical levels: `/source/category/subcategory/data`
3. **Override sparingly**: Only use specific rules when really necessary
4. **Document prefixes**: Ensure each prefix is documented with its destination
5. **Centralized configuration**: All addresses and ports are defined in `network.json`

## Benefits of Hierarchical Routing

- **Simplicity**: More concise and easier to understand configuration
- **Maintainability**: Adding new message types doesn't require modifying the routing table
- **Flexibility**: Ability to create exceptions for specific cases
- **Extensibility**: Makes it easier to add new modules to the system

## Debugging

If problems occur:
- Observe the router logs that display the routing mode used for each message
- Check if a message uses an exact match, a prefix, or the default behavior
- Examine messages broadcast to all (which did not find a matching route)

## How to implement this approach in a new module

For a module to communicate with this routing system, it must:

1. **Be defined** in the `network.json` file with its IP address and port
2. **Prefix its messages** with its identifier (e.g., `/my_module/action/data`)
3. **Listen** on its own port to receive messages intended for it
4. **Be added** to the OSC router's routing table with a prefix (e.g., `/my_module/: ["recipient1", "recipient2"]`)

Here's an implementation example for a generic module:

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
        # Load network configuration
        config = load_network_config()
        self.module_name = module_name
        
        # Check that the module is configured in network.json
        if module_name not in config['osc']:
            raise ValueError(f"Module {module_name} not configured in network.json")
            
        # Get module configuration
        module_config = config['osc'][module_name]
        self.local_ip = module_config['ip']
        self.local_port = module_config['port']
        
        # Client to send messages to the router
        self.client = udp_client.SimpleUDPClient("127.0.0.1", 5005)
        
        # Dispatcher to receive messages
        self.dispatcher = dispatcher.Dispatcher()
        self.setup_handlers()
        
        # OSC server to listen for messages
        self.server = osc_server.ThreadingOSCUDPServer(
            (self.local_ip, self.local_port), self.dispatcher)
    
    def setup_handlers(self):
        """Configure handlers for incoming messages"""
        # For a generic module, we can configure handlers for all
        # possible messages that the module can receive from any source
        self.dispatcher.set_default_handler(self.handle_all_messages)
        
    def handle_all_messages(self, address, *args):
        print(f"Message received: {address} {args}")
        
        # Optional extraction of source module for differentiated processing
        parts = address.split('/')
        if len(parts) > 1:
            source_module = parts[1]
            print(f"  ↳ Source: {source_module}")
        
    def send_message(self, type_msg, *args):
        """Send an OSC message with source module prefix"""
        address = f"/{self.module_name}/{type_msg}"
        self.client.send_message(address, args)
        
    def run(self):
        print(f"Module {self.module_name} started on {self.local_ip}:{self.local_port}")
        self.server.serve_forever()

# Example usage
if __name__ == "__main__":
    module = MyModule("my_module")
    module.send_message("status/active", True)  # Sends /my_module/status/active
    module.run()
```