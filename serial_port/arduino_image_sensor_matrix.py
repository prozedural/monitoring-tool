#########################################################################
#Standalone Programm
#ADNS-2610 optischer Maussensor
#Auslesen der Sensor-Bildmatrix
#benötigt kompilierte OpticalSensorImage.ino
#########################################################################

import serial
import time
from datetime import datetime
import cv2
import matplotlib.pyplot as plt
import numpy as np


#verbinde mit seriellem Port
arduino =   serial.Serial(
            port='COM3',\
            baudrate=250000,\
            timeout=0)


print("Verbunden mit: " + arduino.portstr)


#Zeit zur Initialisierung
time.sleep(1) #in Sekunden


#Bildzähler
counter = 0
img_counter = 0


#Sensorspezifikation ADNS-2610
width       = 18
height      = 18
sensor_size = 324


#generiere Bild gemäß Maussensor (18x18 Pixel)
img = np.zeros((height, width), dtype=np.uint8)

#setze Bildpixel auf beliebige Default-Werte
img.fill(50)

img_stream_raw_data = []
img_replace = np.zeros((sensor_size), dtype=np.uint8)



print('warte auf 1. lesbares Bild')

while (True):

    #lese exakt eine Zeile ein, vgl. Arduino Serial.print("");
    b = arduino.readline()
    
    #wandle das gelesene Byte in String um mit UTF-8 Encoding
    s = str(b, 'utf-8', 'ignore')

    #erzeuge np-Array aus Rohdaten, nutze Trenner 
    img_stream_raw = np.fromstring(s, dtype=np.uint8, sep=',')


    #verarbeite nur vollständig lesbare Bilder
    if img_stream_raw.size >= sensor_size:
   
        print('lesbar Bild Nr.', counter)
        
        img_replace = img_stream_raw[0:sensor_size]


        #wandle 1d-Array in passende Bildmatrix um
        img = img_replace.reshape(height, width)


        #konvertiere Bildwerte in unsigned int
        img = np.uint8(img)
        

        #normalisiere Bild (nutze alle Helligkeitswerte von 0 bis 255
        img_normalized = cv2.normalize(img, img, 0, 255, cv2.NORM_MINMAX)


        #vergrößere Bild ohne Interpolation 
        img_scaled = cv2.resize(img_normalized, None, fx=40.0, fy=40.0, interpolation=cv2.INTER_NEAREST)
        
        #zeige Bild
        cv2.imshow('ADNS-2610 Sensorbild, Skalierung: 4000%', img_scaled)
        cv2.waitKey(1)

        date = str(datetime.now().strftime('%Y-%m-%d_%H-%M'))
        filedir = 'Sensormatrix_Stream/'
        filename = 'Sensormatrix_' +str(img_counter) + '_' + date + '.jpg'
        file = filedir + filename
        cv2.imwrite(file, img_scaled)
        img_counter +=1
    else:
        pass
    
  
    #iteriere Frame
    counter +=1   
   

#trenne Verbindung zum seriellen Port
arduino.close()