#########################################################################
#Standalone Programm
#ADNS-2610 optischer Maussensor
#Auslesen der x-y-Koordinaten
#benötigt kompilierte OpticalSensorCoordinates.ino
#
#
#WEG-ZEIT-MESSUNG (AUTOMATISCHES STARTEN UND STOPPEN DER ZEIT)
#########################################################################


from datetime import datetime
import math
import time
import cv2
import matplotlib.pyplot as plt
import numpy as np

#Serielle Schnittstelle
import serial

#Excel-Datei
from pandas import DataFrame
from openpyxl.workbook import Workbook


#lege Baudrate (Symbole/s) fest
#MUSS mit Arduino-Sketch übereinstimmen
#default Baudrate = 38400
BAUDRATE = 250000

#verbinde mit seriellem Port
arduino =   serial.Serial(
            port='COM3',\
            baudrate=BAUDRATE,\
            timeout=0)

#Zeit zur Initialisierung (in Sekunden)
time.sleep(1)

print("Verbunden mit Port: " + arduino.portstr)



sensor_data = []
sensor_data_default = ['0','0','end']

#Startwerte für x-,y-Absolut
sensor_x_abs = 0
sensor_y_abs = 0

sensor_y_abs_cor = 0

#Listen für Messwerte aus x,y
list_sensor_x_rel = []
list_sensor_x_abs = []
list_sensor_x_real = []

list_sensor_y_rel = []
list_sensor_y_abs = []
list_sensor_y_real = []

list_frame_number = []
list_frame_count_motion = []
list_delta_run_time = []
list_timestamp = []

####################################################################################################
#Variablen aus Arduino

#[val[0] = dx (relative x-Verschiebung)
#[val[1] = dy (relative y-Verschiebung)
#[val[2] = end (LEER)

####################################################################################################


i = 0
start = 0
end = 0
start_time = 0
start_flag = []

#Schalter für Abbruch der Schleife
global setter
setter = True

print()
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
    
    #prüfe ob ALLE Variablen lesbar sind

    if len(sensor_data) != 3:

        #fehlerhafte Frames werden auf default gesetzt
        sensor_data = sensor_data_default
        #print('default')
    

    if (sensor_data[0] == '') or (sensor_data[1] == ''):
        sensor_data = sensor_data_default


    sensor_x_rel        = int(sensor_data[0])
    sensor_y_rel        = int(sensor_data[1])


       
    sensor_x_abs += sensor_x_rel
    
    sensor_x_real = float(sensor_x_abs)

    list_sensor_x_rel.append(sensor_x_rel)
    list_sensor_x_abs.append(sensor_x_abs)
        

    #################################################################################
            
 
    #berechne digitale Absolutverschiebung
    sensor_y_abs += sensor_y_rel

    #berechne reale Absolutverschiebung 
    sensor_y_real = float(sensor_y_abs)

    list_sensor_y_rel.append(sensor_y_rel)
    list_sensor_y_abs.append(sensor_y_abs)

    
    #EXPONENTIALFUNKTION ZUR KORREKTUR
    #exp = abs(sensor_y_rel-1)
    #base = 1.9
    #sensor_y_abs_cor += sensor_y_rel*math.pow(base, exp)


    #Durch die hohe Messfrequenz wird ein Start- und Abbruchkriterium benötigt
    #Variablen sind die    
    #Anzahl Wiederholungen bis Abbruch (-> möglichst klein) 
    num_cancel_values = 500
    
    #minimaler Verfahrweg (geschwindigkeitsabhängig)
    num_min_distance  = 5

 
    #Prüfbedingung für Wagen fährt los
    if (abs(sensor_y_abs) > 0) and (abs(sensor_y_abs) < num_min_distance):
        
        #setze Zeitstempel
        start_time = round(time.time(), 8)
        
        #setze Startmarker auf den i-ten Frame
        start = i
        start_flag.append(start)
     
    if len(start_flag) == 1:
        print('Aufzeichnung gestartet')
        

    ##########################################################################################
    #Die hohe Messfrequenz resultiert in Wertewiederholungen,
    #daher ist das Abbruchkriterium über n Messwerte zu bestimmen
    ##########################################################################################

    #warte auf die ersten i Messwerte
    #und warte bis Wagen losgefahren ist
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
                    
                    #ermittle Zeitdifferenz (Ende - Anfang)
                    delta_time = round((time.time() - start_time), 8)

                    #Abbruchkriterium
                    setter = False
 
    #setze Zeitstempel
    timestamp = round((time.time() - start_time), 8)

    #speichere Zeitstempel in Liste
    list_timestamp.append(timestamp)
    
    #speichere i in Liste
    list_frame_number.append(i)
    
    #Zähler Schleife
    i +=1 


#trenne Verbindung zum seriellen Port
arduino.close()





############################################################################################################
#Datenaufbereitung für Excel
############################################################################################################


#lege Betrachtungsbereich (Bewegung) fest
end = i - num_cancel_values
start_to_end = end - start

#erzeuge neue Frame-Nummern von 0 bis n
list_frame_count_motion  = list(range(0, start_to_end))

date = str(datetime.now().strftime('%Y-%m-%d_%H-%M'))



filename = 'Messwerte_' + date + '_Frames_' + str(start_to_end) + '_Zeit_' + str(round(delta_time, 2)) + 's_y-Abs_' + str(sensor_y_abs) + '_Baud_' + str(BAUDRATE) + '.xlsx'
filedir = 'Bahnverschiebung_Plots_Weg-Zeit/'

file = filedir + filename

print()
print('Frame (Start):', start)
print('Frame (Ende):', i)
print('Frame (Isoliert):', start_to_end)

print('Dauer:', delta_time)
print('Y-Absolut', sensor_y_abs)
print()

print('Verzeichnis:', filedir)
print('Dateiname:', filename)
print()
print('Datei wird gespeichert. Bitte warten ...')


messdaten = DataFrame({'Frame': list_frame_count_motion, 
                       'Zeit in [s]': list_timestamp[start:end],
                       'x-Relativ': list_sensor_x_rel[start:end],
                       'x-Absolut': list_sensor_x_abs[start:end],
                       'y-Relativ': list_sensor_y_rel[start:end],
                       'y-Absolut': list_sensor_y_abs[start:end]
                       })


messdaten.to_excel(file, sheet_name='koordinaten', index=False)

print('Datei gespeichert.')