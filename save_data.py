import config
import sys
import os
from datetime import datetime as DateTime
import cv2

#erzeuge Verzeichnis für Bilder
def createImageFolder():
    print('speichere Bilder')

    #Dateiname (Datum- und Zeitstempel)
    filedir = config.SAVEDATA_BASEDIR+ '/' + DateTime.now().strftime(config.FILENAME_DATE_FORMAT)
    
    #Wechsele in das neue Verzeichnis
    os.mkdir(filedir)
    os.chdir(filedir)


#speichere Bilder im Verzeichnis
def saveImages(file, image):
    if saveStat == True:
       cv2.imwrite(file, image)
    elif saveStat == False:
       pass

#Abfrage Bilder speichern
def saveToDisk():
    getKey = input('Bilder speichern? [j/n] ')
    if getKey == 'j':
        createImageFolder()
        global saveStat
        saveStat = True
    elif getKey == 'n':
        print('weiter ohne Speichern')
    else:
        print('falsche Tastatureingabe')