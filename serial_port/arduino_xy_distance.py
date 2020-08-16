#########################################################################
#Standalone Programm
#ADNS-2610 optischer Maussensor
#Auslesen der x-y-Koordinaten
#benötigt kompilierte OpticalSensorCoordinates.ino
#
#
#WEGMESSUNG (MANUELLES ZIEHEN DES WAGENS; OHNE ZEITMESSUNG)
#########################################################################

import math
import statistics
import serial
import time
from datetime import datetime
import cv2
import matplotlib.pyplot as plt
import numpy as np

#erstellen der Excel-Datei
from pandas import DataFrame
from openpyxl.workbook import Workbook


#lege Baudrate (Symbole/s) fest
#MUSS mit Arduino-Sketch übereinstimmen
BAUDRATE = 250000


#verbinde mit seriellem Port
arduino =   serial.Serial(
            port='COM3',\
            baudrate=BAUDRATE,\
            timeout=0)

#Zeit zur Initialisierung (in Sekunden)
time.sleep(1)

print("Verbunden mit: " + arduino.portstr)


sensor_data = []
sensor_data_default = ['0','0','end']

#Startwerte für x-,y-Absolut
sensor_x_abs = 0
sensor_y_abs = 0
sensor_y_abs_cor = 0


#Listen für Messwerte aus x,y
list_sensor_x_rel = []
list_sensor_x_abs = []

list_sensor_y_rel = []
list_sensor_y_abs = []

list_frame_count_all = []
list_frame_count_motion = []



####################################################################################################
#Variablen aus Arduino

#[val[0] = dx (relative x-Verschiebung)
#[val[1] = dy (relative y-Verschiebung)
#[val[2] = end (LEER)

####################################################################################################

x_abweichung = 0

i = 0
start = 0
start_flag = []

#Schalter für Abbruch der Schleife
global setter
setter = True


print()
print('Wagen manuell bewegen')
print('Warte auf Bewegung ...')

#definiere Abbruchkriterium für Schleife
while (setter == True):
  
    
        #lese exakt eine Zeile ein vgl. Arduino Serial.print("");
        b = arduino.readline()
    
        #wandle das gelesene Byte in String um mit UTF-8 Encoding
        s = str(b, 'utf-8', 'ignore')
    
        #entferne Umbruch aus Messdaten
        s = s.strip("\n\r")

        #trenne Messdaten via Separatorzeichen
        sensor_data = s.split('t')
    

        #################################################################################
        #Korrigiere Messdaten (Rohdaten)

        #prüfe ob alle Messdaten-Felder vorhanden sind
        if len(sensor_data) != 3:

            #setze fehlerhafte Frames auf default
            sensor_data = sensor_data_default

        #prüfe ob Messdaten leer sind
        if (sensor_data[0] == '') or (sensor_data[1] == ''):
            
            #setze leere Felder auf default
            sensor_data = sensor_data_default

        #prüfe ob die Messdaten numerisch sind
        if (sensor_data[0].isnumeric() == False) or (sensor_data[1].isnumeric() == False):
            sensor_data = sensor_data_default

        #################################################################################
        
        sensor_x_rel        = int(sensor_data[0])
        sensor_y_rel        = int(sensor_data[1])


        #berechne Absolutverschiebung
        sensor_x_abs += sensor_x_rel
    
        list_sensor_x_rel.append(sensor_x_rel)
        list_sensor_x_abs.append(sensor_x_abs)
        

        #################################################################################
            
 
        #berechne Absolutverschiebung
        sensor_y_abs += sensor_y_rel

        
        #exp = abs(sensor_y_rel - 1)
        #base = 1.1
        #sensor_y_abs_cor += sensor_y_rel*math.pow(base, exp)


        #berechne reale Absolutverschiebung 
        list_sensor_y_rel.append(sensor_y_rel)
        list_sensor_y_abs.append(sensor_y_abs)
    

        #Werte für Abbruchkriterium
        num_cancel_values = 300
        num_min_distance  = 50
        
        #ZEIGE x-ABWEICHUNG AN
        #if sensor_x_rel == 1:
        #    print('Nr.', i, 'Abweichung in x-Richtung:', sensor_x_rel)
        
        if (abs(sensor_y_rel) > 2):
            print('y-Verschiebung:', abs(sensor_y_rel))

        #Prüfbedingung für Wagen fährt los
        if (abs(sensor_y_abs) > 0) and (abs(sensor_y_abs) < 50):
                
            #setze Startmarker auf den i-ten Frame
            start = i
            start_flag.append(start)
     
        if len(start_flag) == 1:
            print('Aufzeichnung gestartet')


        if (i > num_cancel_values) and (abs(sensor_y_abs) > num_min_distance):

            #separariere zu prüfenden Werteanzahl vom Ende der Liste
            list_sensor_y_abs_cut = list_sensor_y_abs[-num_cancel_values:-1]
        
            #setze Prüfzähler zurück
            cancel = 0

            #vergleiche alle n Werte mit dem letzten Wert
            for value in list_sensor_y_abs_cut:
            
                #iteriere wenn Werte übereinstimmen
                if value == sensor_y_abs:
                    cancel +=1

                    #wenn alle Prüfungspaare aus der Liste gleich sind
                    if cancel == len(list_sensor_y_abs_cut):
                        
                        #Verlasse while-Schleife
                        setter = False


        
        #Zähler Schleife
        i+=1   


#trenne Verbindung zum seriellen Port
arduino.close()


#################################################################################
#Auswertung der Messdaten
#################################################################################


#lege Betrachtungsbereich (Bewegung) fest
end = i - num_cancel_values
start_to_end = end - start

#erzeuge neue Frame-Nummern von 0 bis n
list_frame_count_motion  = list(range(0, start_to_end))


#setze Datumsstempel
date = str(datetime.now().strftime('%Y-%m-%d_%H-%M'))

#Bennenung der Datei
filename = 'Messwerte_' + date + '_Frames_' + str(start_to_end) + 's_y-Abs_' + str(sensor_y_abs) + '_Baud_' + str(BAUDRATE) + '.xlsx'
filedir = 'Bahnverschiebung_Plots_Weg/'
file = filedir + filename

#Darstellung der Messwerte
print()
print('Frame (Start):', start)
print('Frame (Ende):', end)
print('Frame (bereinigt):', start_to_end)
print('y-Absolut', sensor_y_abs)
print('y-Korrektur', sensor_y_abs_cor)
print('y-Relativ (max)', max(list_sensor_y_rel))


#Speicherung der Messwerte
print('Verzeichnis:', filedir)
print('Dateiname:', filename)
print()
print('Datei wird gespeichert. Bitte warten ...')

messdaten = DataFrame({'Frame': list_frame_count_motion, 
                       'x-Relativ': list_sensor_x_rel[start:end],
                       'x-Absolut': list_sensor_x_abs[start:end],
                       'y-Relativ': list_sensor_y_rel[start:end],
                       'y-Absolut': list_sensor_y_abs[start:end]
                       })

#schreibe Daten in Excel-Datei
messdaten.to_excel(file, sheet_name='koordinaten', index=False)

print('Datei gespeichert.')