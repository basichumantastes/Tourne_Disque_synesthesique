#!/usr/bin/env python3

import cv2
import numpy as np
from pythonosc import udp_client
import time

class ColorDetector:
    def __init__(self):
        self.osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9001)
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

    def run(self):
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                # Détection des couleurs
                rgb = self.get_dominant_color(frame)
                hsv = self.get_hsv(rgb)

                # Envoi des données brutes
                self.osc_client.send_message("/color/raw/rgb", list(map(int, rgb)))
                self.osc_client.send_message("/color/raw/hsv", list(map(int, hsv)))
                
                time.sleep(0.1)  # 10 Hz

        except KeyboardInterrupt:
            print("\nArrêt de la capture")
        finally:
            self.cap.release()

def main():
    detector = ColorDetector()
    detector.run()

if __name__ == "__main__":
    main()