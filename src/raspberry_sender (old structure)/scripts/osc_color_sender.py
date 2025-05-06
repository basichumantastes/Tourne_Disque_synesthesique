import cv2
import numpy as np
from pythonosc import udp_client
import time
import json
from ledstrip import LEDStrip
import serial
import signal
import RPi.GPIO as GPIO
import collections

# Taille des buffers pour le lissage des couleurs
COLOR_BUFFER_SIZE = 5
# Facteur alpha pour l'EMA (Exponential Moving Average) - réduit pour plus de stabilité
EMA_ALPHA = 0.0005

def load_config(config_file="config.json"):
    """Charge la configuration à partir d'un fichier JSON."""
    with open(config_file, "r") as f:
        config = json.load(f)
    return config

def get_dominant_color(image):
    """
    Version optimisée: réduit l'image à 10x10 pixels pour accélérer le traitement,
    puis utilise k-means pour extraire la couleur dominante.
    Retourne directement en RGB.
    """
    # Réduire plus drastiquement l'image
    image = cv2.resize(image, (10, 10), interpolation=cv2.INTER_AREA)
    # Aplatir l'image
    pixels = np.float32(image.reshape(-1, 3))
    
    # Paramètres k-means plus rapides
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 5, 1.0)
    _, _, palette = cv2.kmeans(pixels, 1, None, criteria, 1, cv2.KMEANS_RANDOM_CENTERS)
    
    return palette[0][::-1]  # Conversion BGR vers RGB directement

def convert_to_hsv(bgr_color):
    """Convertit une couleur BGR en HSV."""
    color_pixel = np.uint8([[bgr_color]])
    hsv_color = cv2.cvtColor(color_pixel, cv2.COLOR_BGR2HSV)[0][0]
    return hsv_color

def update_ema(current_ema, new_value, alpha=EMA_ALPHA):
    """Calcule la nouvelle valeur EMA basée sur la valeur actuelle et la nouvelle valeur."""
    if current_ema is None:
        return new_value
    return alpha * new_value + (1 - alpha) * current_ema

def signal_handler(sig, frame):
    print("Signal de terminaison reçu :", sig, flush=True)
    raise KeyboardInterrupt

def main():
    # Installer le gestionnaire de signaux pour SIGTERM et SIGINT
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Charger la configuration
    config = load_config()
    osc_ip = config.get("osc_ip", "192.168.0.118") 
    osc_port = config.get("osc_port", 12000)
    rotation_speed = config.get("rotation_speed", 200)
    h_ratio = config.get("h_ratio", 1.0)
    s_ratio = config.get("s_ratio", 1.0)
    v_ratio = config.get("v_ratio", 1.0)
    
    # Buffers pour lisser les changements de couleur (éviter les flashs)
    r_buffer = collections.deque(maxlen=COLOR_BUFFER_SIZE)
    g_buffer = collections.deque(maxlen=COLOR_BUFFER_SIZE)
    b_buffer = collections.deque(maxlen=COLOR_BUFFER_SIZE)
    
    # Initialisation des variables EMA pour RGB et HSV
    r_ema = None
    g_ema = None
    b_ema = None
    h_ema = None
    s_ema = None
    v_ema = None
    
    # Remplir les buffers avec des zéros au démarrage
    for _ in range(COLOR_BUFFER_SIZE):
        r_buffer.append(0)
        g_buffer.append(0)
        b_buffer.append(0)
    
    # Ouverture de la communication série (unique au début)
    try:
        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
        time.sleep(2)  # Attendre l'initialisation de l'Arduino
        ser.write("v0\n".encode())
        print("Commande v0 envoyée sur /dev/ttyUSB0 au démarrage", flush=True)
    except Exception as e:
        print("Erreur lors de l'ouverture du port série :", e, flush=True)
        return

    # Initialisation du client OSC
    osc_client = udp_client.SimpleUDPClient(osc_ip, osc_port)
    
    # Initialisation du ruban LED avec les nouveaux pins
    CLK_PIN = 16  # Changé de 23 à 16
    DAT_PIN = 20  # Changé de 24 à 20
    led_strip = LEDStrip(CLK_PIN, DAT_PIN)
    
    print("Script démarré avec CLK_PIN =", CLK_PIN, "et DAT_PIN =", DAT_PIN, flush=True)
    
    # Pipeline GStreamer optimisée pour la capture vidéo
    gst_pipeline = "libcamerasrc ! video/x-raw,width=320,height=240,framerate=15/1 ! videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1 sync=false"
    print("Pipeline défini :", gst_pipeline, flush=True)
    
    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    timeout = 5
    start_time = time.time()
    while not cap.isOpened() and time.time() - start_time < timeout:
        print("Attente de l'initialisation de la capture...", flush=True)
        time.sleep(0.2)
    
    if not cap.isOpened():
        print("Erreur : la capture n'est pas initialisée.", flush=True)
        ser.close()
        return
    
    # Envoi de la commande de vitesse pour démarrer le moteur
    try:
        command = f"v{rotation_speed}\n"
        ser.write(command.encode())
        print("Commande de vitesse envoyée :", command.strip(), flush=True)
    except Exception as e:
        print("Erreur lors de l'envoi de la commande de vitesse :", e, flush=True)
    
    last_update_time = time.time()
    update_interval = 0.1  # Modifié de 0.05 à 0.1 (100ms entre les mises à jour - 10 Hz)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erreur : Impossible de lire une image.", flush=True)
                time.sleep(0.1)  # Petite pause en cas d'erreur
                continue
            
            # Limiter la fréquence des mises à jour
            current_time = time.time()
            if current_time - last_update_time < update_interval:
                time.sleep(0.001)  # Micropauses pour libérer le CPU
                continue
            
            last_update_time = current_time
            
            # Extraction de la couleur dominante directement en RGB
            rgb_color = get_dominant_color(frame)
            
            # Ajouter les nouvelles valeurs aux buffers
            r_buffer.append(rgb_color[0])
            g_buffer.append(rgb_color[1])
            b_buffer.append(rgb_color[2])
            
            # Moyennes lissées pour éliminer les variations brusques
            r_smooth = sum(r_buffer) / len(r_buffer)
            g_smooth = sum(g_buffer) / len(g_buffer)
            b_smooth = sum(b_buffer) / len(b_buffer)
            
            # Utiliser les valeurs lissées
            rgb_smooth = (r_smooth, g_smooth, b_smooth)
            
            # Conversion en BGR pour HSV avec les valeurs lissées
            bgr_smooth = (b_smooth, g_smooth, r_smooth)
            hsv_color = convert_to_hsv(bgr_smooth)
            
            # Mise à jour des valeurs EMA pour RGB
            r_ema = update_ema(r_ema, r_smooth)
            g_ema = update_ema(g_ema, g_smooth)
            b_ema = update_ema(b_ema, b_smooth)
            
            # Mise à jour des valeurs EMA pour HSV
            h_ema = update_ema(h_ema, hsv_color[0])
            s_ema = update_ema(s_ema, hsv_color[1])
            v_ema = update_ema(v_ema, hsv_color[2])
            
            # Envoi OSC des valeurs originales RGB
            for i, channel in enumerate(['r', 'g', 'b']):
                osc_client.send_message(f"/colour/rgb/{channel}", int(rgb_smooth[i]))
            
            # Envoi OSC des valeurs originales HSV
            for i, channel in enumerate(['h', 's', 'v']):
                osc_client.send_message(f"/colour/hsv/{channel}", int(hsv_color[i]))
            
            # Envoi OSC des valeurs EMA RGB
            osc_client.send_message("/EMA/rgb/r", int(r_ema))
            osc_client.send_message("/EMA/rgb/g", int(g_ema))
            osc_client.send_message("/EMA/rgb/b", int(b_ema))
            
            # Envoi OSC des valeurs EMA HSV
            osc_client.send_message("/EMA/hsv/h", int(h_ema))
            osc_client.send_message("/EMA/hsv/s", int(s_ema))
            osc_client.send_message("/EMA/hsv/v", int(v_ema))
            
            # Mise à jour du ruban LED avec les valeurs lissées
            led_strip.setcolourrgb(*(int(c) for c in rgb_smooth))
            
    except KeyboardInterrupt:
        print("Interruption par l'utilisateur.", flush=True)
    finally:
        cap.release()
        print("Capture libérée.", flush=True)
        try:
            ser.write("v0\n".encode())
            print("Commande v0 envoyée à la fermeture.", flush=True)
        except Exception as e:
            print("Erreur lors de l'envoi de v0 à la fermeture :", e, flush=True)
        print("Attente de 5 secondes avant fermeture du port série...", flush=True)
        time.sleep(5)
        ser.close()
        led_strip.cleanup()

if __name__ == "__main__":
    main()