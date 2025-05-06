#!/usr/bin/env python3

import cv2
import numpy as np
from pythonosc import udp_client
import time
import json
import argparse
import os
from pathlib import Path

class ColorDetector:
    def __init__(self):
        self.setup_camera()

    def setup_camera(self):
        gst_pipeline = "libcamerasrc ! video/x-raw,width=320,height=240,framerate=15/1 ! videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1 sync=false"
        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        
        if not self.cap.isOpened():
            raise RuntimeError("Impossible d'initialiser la capture vidéo")

    def get_dominant_color(self, frame):
        """Extrait la couleur dominante en RGB"""
        frame = cv2.resize(frame, (10, 10), interpolation=cv2.INTER_AREA)
        pixels = np.float32(frame.reshape(-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 5, 1.0)
        _, _, palette = cv2.kmeans(pixels, 1, None, criteria, 1, cv2.KMEANS_RANDOM_CENTERS)
        return palette[0][::-1]  # BGR vers RGB

    def get_hsv(self, rgb):
        """Convertit RGB en HSV"""
        bgr = (rgb[2], rgb[1], rgb[0])
        color_pixel = np.uint8([[bgr]])
        return cv2.cvtColor(color_pixel, cv2.COLOR_BGR2HSV)[0][0]

    def get_frame_colors(self):
        """Capture une frame et retourne les couleurs RGB et HSV"""
        ret, frame = self.cap.read()
        if not ret:
            return None, None

        rgb = self.get_dominant_color(frame)
        hsv = self.get_hsv(rgb)
        return rgb, hsv

    def close(self):
        """Ferme proprement la capture vidéo"""
        if self.cap is not None:
            self.cap.release()

def main():
    # Parsing des arguments
    parser = argparse.ArgumentParser(description="Module de détection de couleurs")
    parser.add_argument("--router-ip", default="127.0.0.1", help="IP du routeur OSC")
    parser.add_argument("--router-port", type=int, default=5005, help="Port du routeur OSC")
    parser.add_argument("--config", action="store_true", 
                        help="Utiliser la configuration du fichier network.json")
    args = parser.parse_args()
    
    # Configuration OSC
    if args.config:
        # Chemin parent pour accéder à network.json
        parent_dir = Path(__file__).resolve().parent.parent
        network_config_path = os.path.join(parent_dir, 'network.json')
        
        # Utiliser la config depuis le fichier
        with open(network_config_path, 'r') as f:
            config = json.load(f)
        osc_config = config['osc']['logic']
        router_ip = osc_config['ip']
        router_port = osc_config['port']
    else:
        # Utiliser les arguments ou les valeurs par défaut
        router_ip = args.router_ip
        router_port = args.router_port
    
    osc_client = udp_client.SimpleUDPClient(router_ip, router_port)
    print(f"Envoi des données couleur à {router_ip}:{router_port}")

    detector = ColorDetector()

    try:
        while True:
            rgb, hsv = detector.get_frame_colors()
            if rgb is not None and hsv is not None:
                osc_client.send_message("/color/raw/rgb", list(map(int, rgb)))
                osc_client.send_message("/color/raw/hsv", list(map(int, hsv)))
            time.sleep(0.1)  # 10 Hz

    except KeyboardInterrupt:
        print("\nArrêt de la capture")
    finally:
        detector.close()

if __name__ == "__main__":
    main()