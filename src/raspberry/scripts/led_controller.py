#!/usr/bin/env python3

"""
Contrôleur pour le bandeau LED
- Reçoit les couleurs via OSC
- Applique les couleurs au bandeau LED
"""

from pythonosc import dispatcher, osc_server
import threading
from lib.ledstrip import LEDStrip

class LEDController:
    def __init__(self, clk_pin=16, dat_pin=20):
        self.led_strip = LEDStrip(clk_pin, dat_pin)
        
        # Configuration OSC
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map("/color/rgb", self.handle_rgb_color)
        
        # Serveur OSC
        self.server = osc_server.ThreadingOSCUDPServer(
            ("127.0.0.1", 9002),  # Port local pour LED
            self.dispatcher
        )
        
    def handle_rgb_color(self, address, r, g, b):
        """Gestion des couleurs RGB reçues via OSC"""
        self.led_strip.setcolourrgb(int(r), int(g), int(b))
        
    def run(self):
        """Démarre le serveur OSC"""
        print(f"LED Controller démarré sur CLK={self.led_strip._LEDStrip__clock}, DAT={self.led_strip._LEDStrip__data}")
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.cleanup()
            
    def cleanup(self):
        """Nettoyage des ressources"""
        if hasattr(self, 'led_strip'):
            self.led_strip.cleanup()

def main():
    controller = LEDController()
    controller.run()

if __name__ == "__main__":
    main()