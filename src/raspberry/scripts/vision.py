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
        self.using_picamera2 = False
        self.picam2 = None
        self.cap = None
        self.setup_camera()

    def setup_camera(self):
        try:
            # Try to use picamera2 (recommended for Raspberry Pi 5)
            from picamera2 import Picamera2
            
            # Initialize the camera
            self.picam2 = Picamera2()
            
            # Configure the camera
            config = self.picam2.create_preview_configuration(
                main={"size": (320, 240), "format": "RGB888"},
                controls={"FrameRate": 15}
            )
            self.picam2.configure(config)
            
            # Start the camera
            self.picam2.start()
            
            # Set cap to None to indicate we're using picamera2
            self.cap = None
            self.using_picamera2 = True
            print("Using picamera2 for camera capture")
            
        except (ImportError, RuntimeError) as e:
            # Fallback to OpenCV if picamera2 is not available
            print(f"Warning: {str(e)}")
            print("Falling back to OpenCV for camera capture")
            gst_pipeline = "libcamerasrc ! video/x-raw,width=320,height=240,framerate=15/1 ! videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1 sync=false"
            self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            self.using_picamera2 = False
            
            if not self.cap.isOpened():
                # Try a simpler pipeline as a last resort
                print("Trying simpler pipeline...")
                gst_pipeline = "libcamerasrc ! video/x-raw,width=320,height=240 ! videoconvert ! video/x-raw,format=BGR ! appsink"
                self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
                
                if not self.cap.isOpened():
                    raise RuntimeError("Impossible d'initialiser la capture vidéo")

    def get_dominant_color(self, frame):
        """Extrait la couleur dominante en RGB"""
        frame = cv2.resize(frame, (10, 10), interpolation=cv2.INTER_AREA)
        pixels = np.float32(frame.reshape(-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 5, 1.0)
        _, _, palette = cv2.kmeans(pixels, 1, None, criteria, 1, cv2.KMEANS_RANDOM_CENTERS)
        
        # Handle BGR vs RGB based on camera source
        if self.using_picamera2:
            return palette[0]  # Already in RGB format
        else:
            return palette[0][::-1]  # BGR to RGB conversion

    def get_hsv(self, rgb):
        """Convertit RGB en HSV"""
        bgr = (rgb[2], rgb[1], rgb[0])
        color_pixel = np.uint8([[bgr]])
        return cv2.cvtColor(color_pixel, cv2.COLOR_BGR2HSV)[0][0]

    def get_frame_colors(self):
        """Capture une frame et retourne les couleurs RGB et HSV"""
        if self.using_picamera2:
            # Get frame from picamera2
            frame = self.picam2.capture_array()
        else:
            # Get frame from OpenCV
            ret, frame = self.cap.read()
            if not ret:
                return None, None

        rgb = self.get_dominant_color(frame)
        hsv = self.get_hsv(rgb)
        return rgb, hsv

    def close(self):
        """Ferme proprement la capture vidéo"""
        if self.using_picamera2 and self.picam2 is not None:
            self.picam2.stop()
        elif self.cap is not None:
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