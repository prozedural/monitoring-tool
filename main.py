#########################################################################
#Main Programm
#########################################################################

#Imaging Source Kamera API
import ctypes as C
import tisgrabber as IC

#Datei- und Verzeichnisfunktionen
import sys
import os

#OpenCV (Bildverarbeitung)
import cv2

#Bildoperationen (Array-Operationen)
import numpy as np

#Grafische Plots
import matplotlib.pyplot as plt
import pandas as pd

#Grafische Benutzerschnittstelle
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import *

#Parallelisierung
import threading
from queue import Queue

#Zeitfunktionen
from datetime import datetime
from datetime import datetime as DateTime
import time

#Datenbank
import sqlite3

#projekteigene Importe
import config
import camera_status
import save_data
import calib_chessboard as cc
import calib_marker as cm


lWidth          = C.c_long()
lHeight         = C.c_long()
iBitsPerPixel   = C.c_int()
COLORFORMAT     = C.c_int()



#Default (Maßstab)
GT_REAL_FACTOR = 0

#Algorithmus Einstellungen
LOWER_THRESH = config.lower_thresh #setze jeden Wert unterhalb Grenze auf 0
ROI_HEIGHT = config.roi_height
DENOISE_KERNEL = config.denoise


#Umrechnungsfaktor
GT_REAL_FACTOR = config.GT_REAL_FACTOR

#realer Markerdurchmesser
MARKER_DIAMETER = config.MARKER_DIAMETER

#Filterkernel
kernel = np.ones((5,5),np.uint8)


############################################################################################################
#Listen
############################################################################################################

img_sim_gt_set = []
img_sim_syn_set = []

list_syn_pos_left = []
list_syn_pos_right = []
list_syn_spalt = []
list_syn_calc_time = []

#Markerdetektion
marker_measured_list = []
marker_average_diameter_list = []
marker_num_found_list = []

#Marker
x_marker_pos_list = []
y_marker_pos_list = []
radius_marker_list = []

#Messdaten
list_id = []
list_spaltbreite = []
list_start_time = []
list_end_time = []
list_calc_time = []

############################################################################################################
############################################################################################################
############################################################################################################


#TIS GRABBER INITIALISIERUNG 
def s(strin):
    if sys.version[0] == "2":
        return strin
    if type(strin) == "byte":
        return strin
    return strin.encode("utf-8")

class CallbackUserdata(C.Structure):
    def __init__(self):
        self.width = 0
        self.height = 0
        self.iBitsPerPixel = 0
        self.buffer_size = 0
        self.oldbrightness = 0
    

#TIS Kamera Callback-Funktion (lese jeden Frame einzeln aus)
def Callback(hGrabber, pBuffer, framenumber, pData):

    if pData.buffer_size > 0:
        image = C.cast(pBuffer, C.POINTER(C.c_ubyte * pData.buffer_size))

        cvMat = np.ndarray(buffer = image.contents,
                        dtype = np.uint8,
                        shape = (pData.height,
                                pData.width,
                                pData.iBitsPerPixel))
        brightness = cv2.mean(cvMat)
        b = int( brightness[0] )
        if b != pData.oldbrightness:
            print( b)
            pData.oldbrightness = b
        

#erzeuge Pointer auf Funktion
Callbackfunc = IC.TIS_GrabberDLL.FRAMEREADYCALLBACK(Callback)

#erzeuge Callback
ImageDescription = CallbackUserdata()    

#erzeuge Kameraobjekt
Camera = IC.TIS_CAM()

#übergebe Funktion (Pointer) und Daten an die Bibliothek
Camera.SetFrameReadyCallback(Callbackfunc, ImageDescription )

#lese alle ankommenden Frames automatisch
Camera.SetContinuousMode(0)


#prüfe Kameraverbindung
camera_status.status(Camera)    

if Camera.IsDevValid():
	print(config.DEVICE, 'ist verbunden')
else:
	print(config.DEVICE, 'ist getrennt')


#Datenbankklasse
class DatabaseManager(object):

    def __init__(self, *db):
        print()

    def close_database(self):
        self.con.close()

    def query(self, arg):
        self.cur.execute(arg)
        self.con.commit()
        return self.cur
   
    def create_database(self):
        
        #erzeuge Dateiname gemäß [Jahr, Monat, Tag - Stunde, Minute, Sekunde]
        db_filename = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        
        #Datenbank-Verzeichnis
        db_locate = config.db_basedir + '/' + db_filename + '.db'

        #stelle Verbindung her
        self.con = sqlite3.connect(db_locate, check_same_thread=False)

        #setze Cursor auf Verbindung
        self.cur = self.con.cursor() 

        #prüfe ob Datenbank bereits angelegt ist
        self.cur.execute("drop TABLE if exists MESSDATEN")

        #erzeuge Table mit Feldern
        sql ='''CREATE TABLE MESSDATEN(
            ID INTEGER,
            SPALT REAL,
            START_TIME TEXT,
            END_TIME TEXT,
            CALC_TIME INTEGER
        )'''


        self.cur.execute(sql)
        print("Datenbank erfolgreich erstellt.")
        print()
        return db_filename


#################################################################################################################################################
#erzeuge Objekt von Datenbank
db = DatabaseManager()

#erstelle initiale Datenbank im Hintergrund
db.create_database()


#Grafische Benutzeroberfläche (GUI)
class App(threading.Thread):

    def __init__(self):
        super().__init__()

        self.start()

    def callback(self):
        self.root.quit()

  
    def run(self):

        #Fenstereinstellungen
        self.root = tk.Tk()
        self.root.protocol("Schließe Fenster", self.callback)
        self.root.title("Quality Monitoring Tool")
        self.root.geometry("900x500")
        self.root.resizable(False,False)
        self.root.iconbitmap('img/icon.ico') 


        #Registerkarten
        tab_parent = ttk.Notebook(self.root)
        tab1 = ttk.Frame(tab_parent)
        tab2 = ttk.Frame(tab_parent)
        tab3 = ttk.Frame(tab_parent)
        tab4 = ttk.Frame(tab_parent)
        tab5 = ttk.Frame(tab_parent)

        #Registertitel
        tab_parent.add(tab1, text=" Live ")
        tab_parent.add(tab2, text=" Kalibrierung ")
        tab_parent.add(tab3, text=" ROI ")
        tab_parent.add(tab4, text=" Einstellungen ")
        tab_parent.add(tab5, text=" Archiv ")


        #GUI Alert-Funktion
        def show_alert_msg(type, text):
            messagebox.showinfo(type, text)
            

        #################################################################################################################################################
        #Formatierung der Bedienelemente
        #x-y-Randabstände der GUI-Elemente
        tx = 25
        ty = 20

        #################################################################################################################################################
        #WIDGETS Nr. 1: LIVE


        #Erzeuge Datum
        def timestamp():
            #erzeuge Zeitstempel 
            timestamp.beg =  datetime.now()

            #Rückgabe Datum
            return str(datetime.now().strftime('%H:%M:%S'))


        #Berechne Zeitdauer
        def duration():

            #erzeuge Zeitstempel 
            end =  datetime.now()

            #Dauer zwischen Start und Stop
            dur = (end - timestamp.beg)
 
            #Rückgabe Dauer
            return dur


        labelLive = tk.Label(tab1, text='Live ' + str(datetime.now().strftime('%d. %m. %Y')), fg="black", font=("helvetica",12))
        labelStatus = tk.Label(tab1, text="Status")
        labelStatusDatabase = tk.Label(tab1, text="Datenbank")
        
        labelDbBegin = tk.Label(tab1, text="Beginn")
        labelDbEnd = tk.Label(tab1, text="Ende")
        labelDbDuration = tk.Label(tab1, text="Dauer")

        entryStatusText = tk.StringVar()
        entryStatus = tk.Entry(tab1, state="readonly", textvariable = entryStatusText)
        entryStatusText.set('IDLE')

        entryStatusDatabaseText = tk.StringVar()
        entryStatusDatabase = tk.Entry(tab1, state="readonly", textvariable = entryStatusDatabaseText)
        entryStatusDatabaseText.set('-')

        entryDbBeginText = tk.StringVar()
        entryDbBegin = tk.Entry(tab1, state="readonly", textvariable = entryDbBeginText)
        entryDbBeginText.set('-')

        entryDbEndText = tk.StringVar()
        entryDbEnd = tk.Entry(tab1, state="readonly", textvariable = entryDbEndText)
        entryDbEndText.set('-')


        entryDbDurationText = tk.StringVar()
        entryDbDuration = tk.Entry(tab1, state="readonly", textvariable = entryDbDurationText)
        entryDbDurationText.set('-')

        
        #erstelle neue Datenbank
        btnCreateDatabase = tk.Button(tab1, text="Starte Aufzeichnung", command = lambda:[
                                                                                    entryStatusDatabaseText.set(db.create_database()), 
                                                                                    entryStatusText.set('GESTARTET'), 
                                                                                    entryDbBeginText.set(timestamp()),
                                                                                    entryDbEndText.set('-'),
                                                                                    entryDbDurationText.set('-')
                                                                                    ])

        #trenne Verbindung zur Datenbank
        btnCloseDatabase = tk.Button(tab1, text="Beende Aufzeichnung", command = lambda:[
   
                                                                                    entryStatusText.set('GESTOPPT'), 
                                                                                    entryDbDurationText.set(duration()), 
                                                                                    entryDbEndText.set(timestamp())  
                                                                                    ])

        
        
        labelInfo = tk.Label(tab1, text='Info', fg="black", font=("helvetica",12))
        labelThreads = tk.Label(tab1, text="Aktive Threads")

        entryThreadsText = tk.StringVar()
        entryThreads = tk.Entry(tab1, state="readonly", bg='red', textvariable = entryThreadsText)
        entryThreadsText.set(threading.active_count())


        #WIDGET Nr.1 - Live Anordnung (Gridmanager)
        labelLive.grid(row=0, column=0, padx=0, pady=ty)

        labelStatus.grid(row=1, column=0, padx=tx, pady=ty, sticky=W)
        entryStatus.grid(row=1, column=1, padx=tx, pady=ty)
        
        labelStatusDatabase.grid(row=2, column=0, padx=tx, pady=ty, sticky=W)
        entryStatusDatabase.grid(row=2, column=1, padx=tx, pady=ty)

        labelDbBegin.grid(row=3, column=0, padx=tx, pady=ty, sticky=W)
        entryDbBegin.grid(row=3, column=1, padx=tx, pady=ty)

        labelDbEnd.grid(row=4, column=0, padx=tx, pady=ty, sticky=W)
        entryDbEnd.grid(row=4, column=1, padx=tx, pady=ty)

        labelDbDuration.grid(row=5, column=0, padx=tx, pady=ty, sticky=W)
        entryDbDuration.grid(row=5, column=1, padx=tx, pady=ty)

        btnCreateDatabase.grid(row=6, column=0, padx=tx, pady=ty)
        btnCloseDatabase.grid(row=6, column=1, padx=tx, pady=ty)

        ttk.Separator(tab1, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=15, sticky='ns')

        labelInfo.grid(row=0, column=3, padx=tx, pady=ty, sticky=W)
        labelThreads.grid(row=1, column=3, padx=tx, pady=ty, sticky=W)
        entryThreads.grid(row=1, column=4, padx=tx, pady=ty)


        #################################################################################################################################################
        #################################################################################################################################################
        #################################################################################################################################################
        #WIDGET Nr. 1: Kalibrierung

        #Linke Seite (Chessboard)
        labelCalibrate = tk.Label(tab2, text='Kalibrierung', fg="black", font=("helvetica",12))

        labelChessCol = tk.Label(tab2, text='Spalten')
        entryChessColText = tk.StringVar()
        entryChessCol = tk.Entry(tab2, textvariable = entryChessColText)
        entryChessColText.set('Spalten')
        
        labelChessRow = tk.Label(tab2, text='Zeilen')
        entryChessRowText = tk.StringVar()
        entryChessRow = tk.Entry(tab2, textvariable = entryChessRowText)
        entryChessRowText.set('Zeilen')

        labelChessDim = tk.Label(tab2, text='Pixelbreite [cm]')
        entryChessDimText = tk.StringVar()
        entryChessDim = tk.Entry(tab2, textvariable = entryChessDimText)
        entryChessDimText.set('Pixelbreite [cm]')

        #Erzeuge Schachbrettmuster
        btnCreateChessboard = tk.Button(tab2, text="Muster erstellen", command = lambda:[cc.create_chessboard( int(entryChessRow.get()), int(entryChessCol.get()), int(entryChessDim.get())), show_alert_msg('Info', 'Muster generiert')])
        
        #Starte Kalibrierung
        btnStartCalibration = tk.Button(tab2, text="Starte Kalibrierung", command = lambda:[])

        chess = PhotoImage(file="img/cb.gif")
        imgChess = Label(tab2, image=chess)

       
        #Rechte Seite (Marker)
        labelMarker = tk.Label(tab2, text='Marker', fg="black", font=("helvetica",12))

        labelMarkerCol = tk.Label(tab2, text='Spalten')
        entryMarkerColText = tk.StringVar()
        entryMarkerCol = tk.Entry(tab2, textvariable = entryMarkerColText)
        entryMarkerColText.set('Spalten')
        
        labelMarkerRow = tk.Label(tab2, text='Zeilen')
        entryMarkerRowText = tk.StringVar()
        entryMarkerRow = tk.Entry(tab2, textvariable = entryMarkerRowText)
        entryMarkerRowText.set('Zeilen')

        labelMarkerDim = tk.Label(tab2, text='Durchmesser [mm]')
        entryMarkerDimText = tk.StringVar()
        entryMarkerDim = tk.Entry(tab2, textvariable = entryMarkerDimText)
        entryMarkerDimText.set('Durchmesser [mm]')

        #erzeuge Marker
        btnCreateMarker = tk.Button(tab2, text="Marker erstellen", command = lambda:[cm.create_marker( int(entryMarkerRow.get()), int(entryMarkerCol.get()), int(entryMarkerDim.get())), show_alert_msg('Info', 'Marker generiert')])

        t2marker = PhotoImage(file="img/marker.gif")
        imgMarker = Label(tab2, image=t2marker)


        #################################################################################################################################################
        #WIDGET Nr.2 - Kalibrierung Anordnung (Gridmanager)

        labelCalibrate.grid(row=0, column=0, padx=tx, pady=ty, sticky=W)
       
        labelChessCol.grid(row=1, column=0, padx=tx, pady=ty, sticky=W)
        labelChessRow.grid(row=2, column=0, padx=tx, pady=ty, sticky=W)
        labelChessDim.grid(row=3, column=0, padx=tx, pady=ty, sticky=W)

        entryChessCol.grid(row=1, column=1, padx=tx, pady=ty)
        entryChessRow.grid(row=2, column=1, padx=tx, pady=ty)
        entryChessDim.grid(row=3, column=1, padx=tx, pady=ty)

        
        imgChess.grid(row=4, column=0, padx=tx, pady=ty, sticky=W)
        btnCreateChessboard.grid(row=4, column=1, padx=tx, pady=ty)
        
        btnStartCalibration.grid(row=5, column=0, padx=tx, pady=ty)

        ttk.Separator(tab2, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=15, sticky='ns')


        labelMarker.grid(row=0, column=3, padx=tx, pady=ty, sticky=W)

        labelMarkerCol.grid(row=1, column=3, padx=tx, pady=ty, sticky=W)
        labelMarkerRow.grid(row=2, column=3, padx=tx, pady=ty, sticky=W)
        labelMarkerDim.grid(row=3, column=3, padx=tx, pady=ty, sticky=W)

        entryMarkerCol.grid(row=1, column=4, padx=tx, pady=ty)
        entryMarkerRow.grid(row=2, column=4, padx=tx, pady=ty)
        entryMarkerDim.grid(row=3, column=4, padx=tx, pady=ty)

        
        imgMarker.grid(row=4, column=3, padx=tx, pady=ty, sticky=W)
        btnCreateMarker.grid(row=4, column=4, padx=tx, pady=ty)
        

        #################################################################################################################################################
        #################################################################################################################################################
        #################################################################################################################################################
        #WIDGET Nr. 3: ROI

        labelRoiSpalt = tk.Label(tab3, text='ROI Spalt (Pixel)', fg="black", font=("helvetica",12))

        spalt = PhotoImage(file="img/spalt_roi.gif")
        imgRoiSpalt = Label(tab3, image=spalt)
     
        labelRoiSpaltx1 = tk.Label(tab3, text='x1')
        entryRoiSpaltx1Text = tk.StringVar()
        entryRoiSpaltx1 = tk.Entry(tab3, textvariable = entryRoiSpaltx1Text)
        entryRoiSpaltx1Text.set(config.roi_spalt_x1)
        
        labelRoiSpaltx2 = tk.Label(tab3, text='x2')
        entryRoiSpaltx2Text = tk.StringVar()
        entryRoiSpaltx2 = tk.Entry(tab3, textvariable = entryRoiSpaltx2Text)
        entryRoiSpaltx2Text.set(config.roi_spalt_x2)
    
        labelRoiSpalty1 = tk.Label(tab3, text='y1')
        entryRoiSpalty1Text = tk.StringVar()
        entryRoiSpalty1 = tk.Entry(tab3, textvariable = entryRoiSpalty1Text)
        entryRoiSpalty1Text.set(config.roi_spalt_y1)

        labelRoiSpalty2 = tk.Label(tab3, text='y2')
        entryRoiSpalty2Text = tk.StringVar()
        entryRoiSpalty2 = tk.Entry(tab3, textvariable = entryRoiSpalty2Text)
        entryRoiSpalty2Text.set(config.roi_spalt_y2)
     
        #Lege Spalt ROI fest
        btnSaveRoiSpalt = tk.Button(tab3, text="Speichern", command = lambda:[
                                                                    config.config_update('roi_spalt_x1', entryRoiSpaltx1.get()),
                                                                    config.config_update('roi_spalt_x2', entryRoiSpaltx2.get()),
                                                                    config.config_update('roi_spalt_y1', entryRoiSpalty1.get()),
                                                                    config.config_update('roi_spalt_y2', entryRoiSpalty2.get())
                                                                    ] )

        
        
        ttk.Separator(tab3, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=15, sticky='ns')


        #ROI MARKER
        labelRoiMarker = tk.Label(tab3, text='ROI Marker (Pixel)', fg="black", font=("helvetica",12))

        marker = PhotoImage(file="img/marker_roi.gif")
        imgRoiMarker = Label(tab3, image=marker)
     
        labelRoiMarkerx1 = tk.Label(tab3, text='x1')
        entryRoiMarkerx1Text = tk.StringVar()
        entryRoiMarkerx1 = tk.Entry(tab3, textvariable = entryRoiMarkerx1Text)
        entryRoiMarkerx1Text.set(config.roi_marker_x1)
        
        labelRoiMarkerx2 = tk.Label(tab3, text='x2')
        entryRoiMarkerx2Text = tk.StringVar()
        entryRoiMarkerx2 = tk.Entry(tab3, textvariable = entryRoiMarkerx2Text)
        entryRoiMarkerx2Text.set(config.roi_marker_x2)
    
        labelRoiMarkery1 = tk.Label(tab3, text='y1')
        entryRoiMarkery1Text = tk.StringVar()
        entryRoiMarkery1 = tk.Entry(tab3, textvariable = entryRoiMarkery1Text)
        entryRoiMarkery1Text.set(config.roi_marker_y1)

        labelRoiMarkery2 = tk.Label(tab3, text='y2')
        entryRoiMarkery2Text = tk.StringVar()
        entryRoiMarkery2 = tk.Entry(tab3, textvariable = entryRoiMarkery2Text)
        entryRoiMarkery2Text.set(config.roi_marker_y2)
     
        #Lege Marker ROI fest
        btnSaveRoiMarker = tk.Button(tab3, text="Speichern", command = lambda:[
                                                                    config.config_update('roi_marker_x1', entryRoiMarkerx1.get()),
                                                                    config.config_update('roi_marker_x2', entryRoiMarkerx2.get()),
                                                                    config.config_update('roi_marker_y1', entryRoiMarkery1.get()),
                                                                    config.config_update('roi_marker_y2', entryRoiMarkery2.get())
                                                                    ] )

       
        #################################################################################################################################################
        #WIDGET Nr.3 - ROI Anordnung (Gridmanager)

        #ROI SPALT
        labelRoiSpalt.grid(row=0, column=0, padx=tx, pady=ty, sticky=W)
        
        imgRoiSpalt.grid(row=1, column=0, columnspan=2, padx=tx, pady=ty, sticky=W)

        entryRoiSpaltx1.grid(row=2, column=1, padx=tx, pady=10)
        labelRoiSpaltx1.grid(row=2, column=0, padx=tx, pady=10, sticky=W)

        entryRoiSpaltx2.grid(row=3, column=1, padx=tx, pady=10)
        labelRoiSpaltx2.grid(row=3, column=0, padx=tx, pady=10, sticky=W)

        entryRoiSpalty1.grid(row=4, column=1, padx=tx, pady=10)
        labelRoiSpalty1.grid(row=4, column=0, padx=tx, pady=10, sticky=W)

        entryRoiSpalty2.grid(row=5, column=1, padx=tx, pady=10)
        labelRoiSpalty2.grid(row=5, column=0, padx=tx, pady=10, sticky=W)

        btnSaveRoiSpalt.grid(row=6, column=0, padx=tx, pady=ty)



        #ROI MARKER
        labelRoiMarker.grid(row=0, column=3, padx=tx, pady=ty, sticky=W)
        
        imgRoiMarker.grid(row=1, column=3, columnspan=2, padx=tx, pady=ty, sticky=W)

        entryRoiMarkerx1.grid(row=2, column=4, padx=tx, pady=10)
        labelRoiMarkerx1.grid(row=2, column=3, padx=tx, pady=10, sticky=W)

        entryRoiMarkerx2.grid(row=3, column=4, padx=tx, pady=10)
        labelRoiMarkerx2.grid(row=3, column=3, padx=tx, pady=10, sticky=W)

        entryRoiMarkery1.grid(row=4, column=4, padx=tx, pady=10)
        labelRoiMarkery1.grid(row=4, column=3, padx=tx, pady=10, sticky=W)

        entryRoiMarkery2.grid(row=5, column=4, padx=tx, pady=10)
        labelRoiMarkery2.grid(row=5, column=3, padx=tx, pady=10, sticky=W)

        btnSaveRoiMarker.grid(row=6, column=3, padx=tx, pady=ty)


        #################################################################################################################################################
        #################################################################################################################################################
        #################################################################################################################################################
        #WIDGET Nr. 4: ARCHIV


        #lese Einträge Datenbank für Listbox
        def show_dbtable(db):
            dir = config.db_basedir +'/'+ db
            conn = sqlite3.connect(dir)
            print('')
            print('Datenbank: ', db)
            print('')
            print(pd.read_sql_query("SELECT * FROM MESSDATEN", conn))
            print('')
            print('-------------------------------------------------------------')


        #speicher Datenbank als .txt-Datei
        def save_db_as_txt():  
            
            #verhindere Index-Error
            if(lbox.curselection()):
                
                #lese Dateiname mit Dateiendung
                db_name_ext = lbox.get(lbox.curselection()[0])

                #lösche Dateiendung (Anzeige)
                db_name = db_name_ext[:-3]

                #Speicherort
                dir = config.db_basedir +'/'+ db_name_ext
                txtoutput = config.db_basedir +'/'+ db_name + '.txt'

                #verbinde mit Datenbank
                conn = sqlite3.connect(dir)
            
                #erzeuge Dataframe aus Datenbank (Pandas)
                df = pd.read_sql_query("SELECT * FROM MESSDATEN", conn)

                #formatiere Dataframe
                df.to_csv(txtoutput, sep='\t', index=False, mode='a')
            else:
                pass



        labelDb = tk.Label(tab5, text="Datenbanken", fg="black", font=("helvetica",12))

        db_filelist = os.listdir(config.db_basedir)
        lbox = tk.Listbox(tab5, height=20, width=80)
 

        #durchsuche alle .db-Dateien im Verzeichnis
        for file in db_filelist:
            if file.endswith(".db"):
                lbox.insert(tk.END, file)

        #aktiviere Listbox-Selektion
        def onselect(event):
            w = event.widget

            #vermeide Index-Error
            if(w.curselection()):
                idx = w.curselection()[0]  

                value = w.get(idx)
           
                show_dbtable(value)
            else:
                pass
    
        #zeige Listbox-Einträge
        lbox.bind('<<ListboxSelect>>', onselect)

    
        #################################################################################################################################################
        #WIDGET Nr.4 - Archiv Anordnung (Gridmanager)

        btnCreateDbTxt = tk.Button(tab5, text="Save as txt-file", command = lambda:[save_db_as_txt()] )
        btnCreateDbTxt.grid(row=1, column=2, padx=tx, pady=0)

        labelDb.grid(row=0, column=0, padx=0, pady=ty)
        lbox.grid(row=1, column=0, columnspan=2, rowspan=5, padx=tx, pady=ty)



        #################################################################################################################################################
        #################################################################################################################################################
        #################################################################################################################################################
        #WIDGET Nr. 5: Einstellungen


        ttk.Separator(tab4, orient=tk.VERTICAL).grid(column=4, row=0, rowspan=15, sticky='ns')

        labelKonst = tk.Label(tab4, text="Konstanten", fg="black", font=("helvetica",12))
        labelVar = tk.Label(tab4, text="Variablen", fg="black", font=("helvetica",12))

        #Kamera
        labelDevice = tk.Label(tab4, text="Kamera")
        entryDeviceText = tk.StringVar()
        entryDevice = tk.Entry(tab4, state="readonly", textvariable = entryDeviceText)
        entryDeviceText.set(config.DEVICE)

        #Bildrate
        labelDeviceFPS = tk.Label(tab4, text="Kamera FPS")
        entryDeviceFPSText = tk.StringVar()
        entryDeviceFPS = tk.Entry(tab4, state="readonly", textvariable = entryDeviceFPSText)
        entryDeviceFPSText.set(config.DEVICE_FPS)

        #Bildbreite
        labelDeviceWidth = tk.Label(tab4, text="Bildbreite (Pixel)")
        entryDeviceWidthText = tk.StringVar()
        entryDeviceWidth = tk.Entry(tab4, state="readonly", textvariable = entryDeviceWidthText)
        entryDeviceWidthText.set(config.DEVICE_WIDTH)

        #Bildhöhe
        labelDeviceHeight = tk.Label(tab4, text="Bildhöhe (Pixel)")
        entryDeviceHeightText = tk.StringVar()
        entryDeviceHeight = tk.Entry(tab4, state="readonly", textvariable = entryDeviceHeightText)
        entryDeviceHeightText.set(config.DEVICE_HEIGHT)

        #Entrauschen
        labelDenoise = tk.Label(tab4, text="Entrauschen (3,5,7,9)")
        entryDenoiseText = tk.StringVar()
        entryDenoise = tk.Entry(tab4, textvariable = entryDenoiseText)
        entryDenoiseText.set(config.denoise)
        btnDenoise = tk.Button(tab4, text="Speichern", command = lambda:[config.config_update('denoise', entryDenoise.get())] )

        #Marker
        labelMarker = tk.Label(tab4, text="⌀ Marker [mm]")
        entryMarkerText = tk.StringVar()
        entryMarker = tk.Entry(tab4, textvariable = entryMarkerText)
        entryMarkerText.set(config.MARKER_DIAMETER)
        btnMarker = tk.Button(tab4, text="Speichern", command = lambda:[config.config_update('marker_diameter', entryMarker.get())] )

        #LOWER_THRESH
        labelLowerThresh = tk.Label(tab4, text="Lower Threshold <255")
        entryLowerThreshText = tk.StringVar()
        entryLowerThresh = tk.Entry(tab4, textvariable = entryLowerThreshText)
        entryLowerThreshText.set(config.lower_thresh)
        btnLowerThresh = tk.Button(tab4, text="Speichern", command = lambda:[config.config_update('lower_thresh', entryLowerThresh.get())] )

        #Datenbank
        labelDbDir = tk.Label(tab4, text="Datenbank Verzeichnis")
        entryDbDirText = tk.StringVar()
        entryDbDir = tk.Entry(tab4, textvariable = entryDbDirText)
        entryDbDirText.set(config.db_basedir)
        btnDbDir = tk.Button(tab4, text="Speichern", command = lambda:[config.config_update('db_basedir', entryDbDir.get())] )


        #WIDGET Nr.5 - Einstellungen Anordnung (Gridmanager)

        #linke Seite
        labelKonst.grid(row=0, column=0, padx=tx, pady=ty)

        labelDevice.grid(row=1, column=0, padx=tx, pady=ty)
        entryDevice.grid(row=1, column=1, padx=tx, pady=ty)

        labelDeviceFPS.grid(row=2, column=0, padx=tx, pady=ty)
        entryDeviceFPS.grid(row=2, column=1, padx=tx, pady=ty)

        labelDeviceWidth.grid(row=3, column=0, padx=tx, pady=ty)
        entryDeviceWidth.grid(row=3, column=1, padx=tx, pady=ty)

        labelDeviceHeight.grid(row=4, column=0, padx=tx, pady=ty)
        entryDeviceHeight.grid(row=4, column=1, padx=tx, pady=ty)
        
        #rechte Seite
        labelVar.grid(row=0, column=6, padx=tx, pady=ty)

        labelMarker.grid(row=1, column=6, padx=tx, pady=ty)
        entryMarker.grid(row=1, column=7, padx=tx, pady=ty)
        btnMarker.grid(row=1, column=8, padx=tx, pady=ty)


        labelDenoise.grid(row=2, column=6, padx=tx, pady=ty)
        entryDenoise.grid(row=2, column=7, padx=tx, pady=ty)
        btnDenoise.grid(row=2, column=8, padx=tx, pady=ty)
        

        labelLowerThresh.grid(row=3, column=6, padx=tx, pady=ty)
        entryLowerThresh.grid(row=3, column=7, padx=tx, pady=ty)
        btnLowerThresh.grid(row=3, column=8, padx=tx, pady=ty)


        labelDbDir.grid(row=4, column=6, padx=tx, pady=ty)
        entryDbDir.grid(row=4, column=7, padx=tx, pady=ty)
        btnDbDir.grid(row=4, column=8, padx=tx, pady=ty)




        tab_parent.pack(expand=1, fill='both')

        self.root.mainloop()


#Erzeuge App-Objekt
app = App()


#Kamera startet Aufzeichnung
if (Camera.IsDevValid() == 1):

    #Videoformat (Breite x Höhe als Textstring) z. B.  ("Y800 (640x480)")
    dev_videoFormat = 'Y800 ('+str(config.DEVICE_WIDTH)+'x'+str(config.DEVICE_HEIGHT)+')'
    Camera.SetVideoFormat(dev_videoFormat)
    
    #Bildrate     
    Camera.SetFrameRate(config.DEVICE_FPS)

    #Farbtiefe (Y800 = 8bit)
    Camera.SetFormat(IC.SinkFormats.Y800)
   
    print('Kamera: ', dev_videoFormat, config.DEVICE_FPS, ' fps')


    #Starte Bildübertragung
    Camera.StartLive(0)

    #Framezähler
    j = 0

    try:
        while ( True ):
            #Framezähler
            list_id.append(j)

            #Zeit-/Performanzmessung (Start)
            t0 = time.perf_counter()
            
            
            start_time = str(datetime.now())
            list_start_time.append(start_time)

            #Lese Livebild ein
            Camera.SnapImage()
            device_image = Camera.GetImageEx()
            
            #8bit unsigned int (Konvertierung für OpenCV)
            device_image.astype('uint8')

            device_algo = cv2.resize(device_image, (0,0), fx=.25, fy=.25)

            ################################################################################################################################
            #Lege Bildausschnitt (ROI) für Spalt fest
           
            syn_spalt = device_image.copy()
    
            syn_spalt_roi = syn_spalt[config.roi_spalt_y1:config.roi_spalt_y2, config.roi_spalt_x1:config.roi_spalt_x2]

            syn_spalt_roi = np.uint8(syn_spalt_roi)

            #Entrauschen des Bildes
            blur = cv2.GaussianBlur(syn_spalt_roi,(DENOISE_KERNEL, DENOISE_KERNEL),0)
        
            #Binarisierung des Bildes
            ret1,thresh = cv2.threshold(blur, LOWER_THRESH, 255,cv2.THRESH_TOZERO)
    
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            #finde Konturen
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


            #finde Bounding-Box
            bound_x, bound_y, bound_w, bound_h = cv2.boundingRect(thresh)

            #Speichere linke und rechte Spaltenseite
            syn_pos_left = bound_x
            syn_pos_right = bound_x + bound_w
            syn_width = bound_w
            syn_spalt = (syn_pos_right - syn_pos_left)

            #Speichere Positionen in Liste
            list_syn_pos_left.append(syn_pos_left)
            list_syn_pos_right.append(syn_pos_right)
            list_syn_spalt.append(syn_spalt)


            ###################################################################################################
            #MARKER
            
            #ROI = image[y1:y2, x1:x2]

            #setze ROI für Marker-Detektion
            syn_detect = device_image.copy()

            syn_detect_roi = syn_detect[config.roi_marker_y1:config.roi_marker_y2, config.roi_marker_x1:config.roi_marker_x2]

            #Entferne hochfrequentes Rauschen mittels Filter-Kernel
            blur = cv2.GaussianBlur(syn_detect_roi,(DENOISE_KERNEL, DENOISE_KERNEL),0)

    
            #erzeuge Binärbild mit hohem Kontrast
            ret,thresh_marker = cv2.threshold(blur, 0,255,cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            #Finde alle Konturen
            contours,hierarchy = cv2.findContours(thresh_marker, 1, 2)

            #Initalisierung Marker
            marker_num_found = 0
            marker_num_found = len(contours) - 1

            #speichere Kandidaten in Liste
            marker_num_found_list.append(marker_num_found)

            #falls Marker detektiert, prüfe diese
            if marker_num_found > 1:
                for marker in range(0, marker_num_found):
                    cnt = contours[marker]
                    
                    #finde alle verfügbaren Kreise
                    for cn in cnt:
                        (x_marker_pos, y_marker_pos), r = cv2.minEnclosingCircle(cnt)
                        
                        diameter = 2 * r * GT_REAL_FACTOR
            
                
                    #füge alle Durchmesser in die Liste ein
                    marker_measured_list.append(diameter)

                    print('Position', x_marker_pos ,y_marker_pos)
                    x_marker_pos_list.append(x_marker_pos)
                    y_marker_pos_list.append(y_marker_pos)
                    radius_marker_list.append(r)
            

            #berechne Marker-Durchmesser (Durchschnitt)
            average_marker_diameter = sum(marker_measured_list) / marker_num_found
            marker_average_diameter_list.append(average_marker_diameter)
    

            #setze Listenwerte zurück
            marker_measured_list.clear()

            #bereite Marker für Fensterausgabe vor (Farbe)
            marker_roi_out = cv2.cvtColor(thresh_marker, cv2.COLOR_GRAY2RGB)
    

            if marker_num_found > 0:
                for el in range(marker_num_found):
                    marker_roi_out = cv2.circle(marker_roi_out, (int(x_marker_pos_list[el]), int(y_marker_pos_list[el])), radius= int(radius_marker_list[el]), color=(0, 0, 255), thickness=2)
            else:
                pass
            
            marker_roi_out = cv2.resize(marker_roi_out, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_CUBIC)


            #Zeitdauer in Sekunden
            dt = round((time.perf_counter() - t0), 4)
            list_calc_time.append(dt)

            end_time = str(datetime.now())
            list_end_time.append(end_time)
            
            list_spaltbreite.append(j*2)
            

            syn_img_output = device_image.copy()
            syn_img_output = cv2.cvtColor(syn_img_output, cv2.COLOR_GRAY2RGB)
            syn_img_output = cv2.rectangle(syn_img_output, (bound_x, config.roi_spalt_y1), (bound_x + bound_w, config.roi_spalt_y1 + config.roi_spalt_y2), (0,255,0), 2)


            #Verkleinere Bild
            syn_img_output = cv2.resize(syn_img_output, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_CUBIC)

            
            #OpenCV Fenster (Analyse-Modus)
            #cv2.imshow('Marker Detection view 50% ', marker_roi_out)
            #cv2.imshow('Spalt Detection view 30% ', syn_img_output)
            #cv2.imshow('Spaltgröße ', syn_spalt_roi)
            #cv2.waitKey(1)


            #schreibe alle Messdaten in die Datenbank
            try:
               db.query(f'INSERT INTO MESSDATEN VALUES ("{list_id[j]}","{list_spaltbreite[j]}", "{list_start_time[j]}", "{list_end_time[j]}", "{list_calc_time[j]}")')

            except sqlite3.ProgrammingError as e:
                print(e)
                pass


            #setze Listen zurück
            x_marker_pos_list.clear()
            y_marker_pos_list.clear()
            radius_marker_list.clear()
            
            
            #iteriere Frame
            j=j+1


    except KeyboardInterrupt:
            #beende Kameraübertragung
            Camera.StopLive()

            #schliesse offene OpenCV-Fenster
            #cv2.destroyAllWindows() 
else:
    #keine Kamera gefunden
    print( "keine Kamera gefunden")