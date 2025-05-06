#!/usr/bin/python

import time
import RPi.GPIO as GPIO
import collections

class LEDStrip:
    def __init__(self, clock, data, smoothing_factor=0.15, buffer_size=5):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.__clock = clock
        self.__data = data
        
        # Configuration des pins
        GPIO.setup(self.__clock, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.__data, GPIO.OUT, initial=GPIO.LOW)
        
        # Variables pour le lissage des couleurs
        self.__last_red = 0
        self.__last_green = 0
        self.__last_blue = 0
        self.__smoothing_factor = smoothing_factor
        
        # Buffer circulaire pour lissage
        self.__buffer_size = buffer_size
        self.__red_buffer = collections.deque(maxlen=buffer_size)
        self.__green_buffer = collections.deque(maxlen=buffer_size)
        self.__blue_buffer = collections.deque(maxlen=buffer_size)
        
        # Initialiser les buffers avec des zéros
        for _ in range(buffer_size):
            self.__red_buffer.append(0)
            self.__green_buffer.append(0)
            self.__blue_buffer.append(0)
            
        print(f"LED Strip initialisé sur CLK={clock}, DAT={data}")
        
    def __clk_rise(self):
        """Génère une impulsion d'horloge avec timing précis - exactement comme dans RGBdriver.cpp"""
        GPIO.output(self.__clock, GPIO.LOW)
        time.sleep(20/1000000)  # Délai exact de 20 microsecondes comme dans le code Arduino
        GPIO.output(self.__clock, GPIO.HIGH)
        time.sleep(20/1000000)  # Délai exact de 20 microsecondes comme dans le code Arduino

    def __send32zero(self):
        """Envoie 32 bits à zéro - utilisé pour la synchronisation"""
        for _ in range(32):
            GPIO.output(self.__data, GPIO.LOW)
            self.__clk_rise()

    def __take_anti_code(self, dat):
        """Implémentation exacte de la fonction TakeAntiCode du code Arduino"""
        tmp = 0
        
        if (dat & 0x80) == 0:
            tmp |= 0x02
            
        if (dat & 0x40) == 0:
            tmp |= 0x01
            
        return tmp

    def __dat_send(self, dx):
        """Implémentation exacte de la fonction DatSend du code Arduino"""
        for _ in range(32):
            if (dx & 0x80000000) != 0:
                GPIO.output(self.__data, GPIO.HIGH)
            else:
                GPIO.output(self.__data, GPIO.LOW)
                
            dx <<= 1
            self.__clk_rise()

    def __smooth_color(self, new_value, last_value):
        """Applique un lissage exponentiel à la valeur de couleur"""
        return int(last_value + self.__smoothing_factor * (new_value - last_value))

    def setcolourrgb(self, red, green, blue):
        """Version améliorée avec lissage temporel et protocole exact"""
        # Limiter les valeurs entre 0 et 255
        red = max(0, min(255, int(red)))
        green = max(0, min(255, int(green)))
        blue = max(0, min(255, int(blue)))
        
        # Ajouter au buffer circulaire
        self.__red_buffer.append(red)
        self.__green_buffer.append(green)
        self.__blue_buffer.append(blue)
        
        # Calculer la moyenne des buffers pour un premier lissage
        avg_red = sum(self.__red_buffer) / len(self.__red_buffer)
        avg_green = sum(self.__green_buffer) / len(self.__green_buffer)
        avg_blue = sum(self.__blue_buffer) / len(self.__blue_buffer)
        
        # Appliquer un lissage exponentiel
        smooth_red = self.__smooth_color(avg_red, self.__last_red)
        smooth_green = self.__smooth_color(avg_green, self.__last_green)
        smooth_blue = self.__smooth_color(avg_blue, self.__last_blue)
        
        # Mettre à jour les dernières valeurs
        self.__last_red = smooth_red
        self.__last_green = smooth_green
        self.__last_blue = smooth_blue
        
        # Conversion en entiers pour envoi
        final_red = int(smooth_red)
        final_green = int(smooth_green)
        final_blue = int(smooth_blue)
        
        # Commencer exactement comme dans le code Arduino
        self.__send32zero()  # Correspond à begin() dans RGBdriver
        
        # Construction du mot de 32 bits comme dans SetColor
        dx = 0
        dx |= (0x03 << 30)
        dx |= (self.__take_anti_code(final_blue) << 28)
        dx |= (self.__take_anti_code(final_green) << 26)
        dx |= (self.__take_anti_code(final_red) << 24)
        
        dx |= (final_blue << 16)
        dx |= (final_green << 8)
        dx |= final_red
        
        # Envoi des données
        self.__dat_send(dx)
        
        # Terminer exactement comme dans le code Arduino
        self.__send32zero()  # Correspond à end() dans RGBdriver

    def setcolourwhite(self):
        self.setcolourrgb(255, 255, 255)

    def setcolouroff(self):
        self.setcolourrgb(0, 0, 0)

    def setcolourred(self):
        self.setcolourrgb(255, 0, 0)

    def setcolourgreen(self):
        self.setcolourrgb(0, 255, 0)

    def setcolourblue(self):
        self.setcolourrgb(0, 0, 255)

    def setcolourhex(self, hex_color):
        try:
            hex_value = int(hex_color, 16)
            red = (hex_value >> 16) & 0xFF
            green = (hex_value >> 8) & 0xFF
            blue = hex_value & 0xFF
            self.setcolourrgb(red, green, blue)
        except Exception as e:
            print(f"Erreur lors de la conversion de la valeur hexadécimale {hex_color}: {e}")

    def cleanup(self):
        """Nettoie proprement les ressources GPIO"""
        self.setcolouroff()  # Éteindre les LEDs
        GPIO.cleanup([self.__clock, self.__data])
        print("LED Strip nettoyé")