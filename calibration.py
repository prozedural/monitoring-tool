import config
import camera_status
import save_data
import ctypes as C
import tisgrabber as IC
import numpy as np
import sys
import os
import cv2
import matplotlib.pyplot as plt
import math
from datetime import datetime as DateTime



lWidth          = C.c_long()
lHeight         = C.c_long()
iBitsPerPixel   = C.c_int()
COLORFORMAT     = C.c_int()


#Erstelle Kameraobjekt
Camera         = IC.TIS_CAM()

#Terminierungs Kriterium
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

#Felder des Schachbrettmusters
#Breite x Höhe
pattern_size = (config.chessboard_w, config.chessboard_h)


#Bereite Objektpunkte vor, gemäß (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((np.prod(pattern_size),3), np.float32)
objp[:, :2] = np.indices(pattern_size).T.reshape(-1,2)


#Arrays für Objektpunkte und Bildpunkte
objpoints = [] # 3d-Punkte im Realraum
imgpoints = [] # 2d-Punkte im BIld


camera_status.status(Camera)    


if Camera.IsDevValid() == 1:

    #lege Videoformat (Breite x Höhe) fest
    device_videoFormat = 'Y800 ('+str(config.DEVICE_WIDTH)+'x'+str(config.DEVICE_HEIGHT)+')'
    Camera.SetVideoFormat(device_videoFormat)
    print('Kamera: ', device_videoFormat, config.DEVICE_FPS, ' fps')


    #Bildrate       
    Camera.SetFrameRate(config.DEVICE_FPS)


    #Farbtiefe 8bit
    Camera.SetFormat(IC.SinkFormats.Y800)

    #Starte Videostream
    Camera.StartLive(0)


    print('Zum Kalibrierung', config.key_calibrate, 'drücken')

    run = True
    try:
        while ( run ):
            #zeichne Bild auf
            Camera.SnapImage()
            uncalibrated_img_stream = Camera.GetImageEx()
            uncalibrated_img_stream = uncalibrated_img_stream.astype('uint8')
            
            #Skaliere Bild
            uncalibrated_img_stream = cv2.resize(uncalibrated_img_stream, (0,0), fx=.25, fy=.25)
            
            #make a copy to draw the overlay on
            #Bildkopie zum 
            uncalibrated_img_stream_view = uncalibrated_img_stream.copy()


            #RGB Version (farbige Darstellung)
            uncalibrated_img_stream_view = cv2.cvtColor(uncalibrated_img_stream_view, cv2.COLOR_GRAY2RGB)

            #Höhe, Breite des Videostreams
            h, w = uncalibrated_img_stream.shape[:2]

            #Echtzeit Kantendetektion
            margin = 25
            rect_startpoint = (margin, margin)
            rect_endpoint = (w - margin, h - margin)
            
            #Kante detektiert: grün
            color_detected = (0, 255, 0)    
            
            #Kante nicht detektiert: rot
            color_undetected = (0, 0, 255) 
            
            #Linienstärke
            thickness = 1   


            #finde und speichere gefundene Ecken in Array
            corner_is_found, corners = cv2.findChessboardCorners(uncalibrated_img_stream, (pattern_size), None)


            if corner_is_found == True:
                objpoints = [objp]

                #speichere letzten Frame (mit gefundenen Kanten)
                dev1_uncalibrated = uncalibrated_img_stream.copy()

                corners2 = cv2.cornerSubPix(uncalibrated_img_stream,corners,(11,11),(-1,-1),criteria)
                
                imgpoints = [corners2]

                #zeichne Fenster für detektierte Kanten
                cv2.drawChessboardCorners(uncalibrated_img_stream_view, (pattern_size), corners2, corner_is_found)
                cv2.putText(uncalibrated_img_stream_view,'Muster detektiert',(margin, h-5), cv2.FONT_HERSHEY_SIMPLEX, .5, (color_detected), 1, cv2.LINE_AA)
                cv2.rectangle(uncalibrated_img_stream_view, rect_startpoint, rect_endpoint, color_detected, thickness)


            else:
                #zeichne Fenster für nicht detektierte Kanten
                cv2.putText(uncalibrated_img_stream_view,'Muster nicht gefunden, bitte Position korrigieren',(margin, h-5), cv2.FONT_HERSHEY_SIMPLEX, .5, (color_undetected), 1, cv2.LINE_AA)
                cv2.rectangle(uncalibrated_img_stream_view, rect_startpoint, rect_endpoint, color_undetected, thickness)


            #draw window content
            cv2.putText(uncalibrated_img_stream_view,'Wenn sich das Muster innerhalb des Rahmens befindet, drücke \'' + config.key_calibrate + '\' zum kalibrieren',(margin, margin-5), cv2.FONT_HERSHEY_SIMPLEX, .5, (color_detected), 1, cv2.LINE_AA)
          
           

            cv2.imshow('Echtzeit Kamerakalibrierung: ' + str(config.DEVICE), uncalibrated_img_stream_view)
 
            key = cv2.waitKey(1) 
            
            #press c to go on
            if key == ord(config.key_calibrate):
                print('Starte Kalibrierung ...')
                                
                #save uncalibrated frame                
                cv2.imwrite('calibration/dev1_uncalibrated.bmp', dev1_uncalibrated)

                print('Frame gespeichert')
                
            else:
                continue

            cv2.destroyAllWindows()
            print('Berechne Verzerrung ...')
            

            ret, camera_matrix, dist_coef, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, (w, h), None, None)
            

            #Kalibrierungsinformationen
            #print('ret ', ret)
            #print('camera_matrix ', camera_matrix)
            #print('dist ', dist_coef)
            #print('rvecs ', rvecs)
            #print('tvecs ', tvecs)

           
            newcameramtx, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coef, (w,h), 1, (w,h))

            #Kalibrierter Frame
            dev1_calibrated = cv2.undistort(dev1_uncalibrated, camera_matrix, dist_coef, None, newcameramtx)

            
            #speichere Kalibrierung
            cv2.imwrite('calibration/dev1_calibrated.bmp', dev1_calibrated)

            #zeige unkalibrierte Version 50%          
            overlay = cv2.addWeighted(dev1_uncalibrated, 0.5, dev1_calibrated, 1, 0)

            cv2.imshow('overlay: calibrated - uncalibrated', overlay)
            cv2.imwrite('calibration/overlay.bmp', overlay)

            cv2.waitKey(500)
            cv2.destroyAllWindows()
            run = False

             
            
            #Berechne Skalierung des Musters

            #sortiere BIldpunkte in 2d-Array gemäß [x0, y0], [x1, y1], [xn, yn]
            square_dist_uncal = np.reshape(imgpoints, (42,2), order='C')
            square_dist_pyt_uncal = []

            for i in range(1, np.size(square_dist_uncal, 0)):
                dx = square_dist_uncal[i,0] - square_dist_uncal[i-1, 0]
                dy = square_dist_uncal[i,1] - square_dist_uncal[i-1, 1]

                square_dist_pyt_uncal.append(math.sqrt(dx**2 + dy**2))
               
                #print('dx: ',i, dx, 'dy ', dy, '\t', square_dist_pyt_uncal[i-1])


            max_square_dist_uncal = square_dist_pyt_uncal[0]*2

            for el in square_dist_pyt_uncal:
                if el > max_square_dist_uncal:
                    square_dist_pyt_uncal.remove(el)
                else:
                    pass
           

            #####################################
            #Unkalibrierte Vermessung
            #####################################

            #erstelle Werte für Diagramm
            x = np.arange(len(square_dist_pyt_uncal))
            y = square_dist_pyt_uncal
            sq_mittelwert_uncal = sum(square_dist_pyt_uncal)/len(square_dist_pyt_uncal)

            print('Mittelwert (unkalibrierte Kamera) :\t', sq_mittelwert_uncal, ' px')


            #fülle Liste mit Mittelwerten 
            sq_mittelwert_container_uncal = []
            for i in range(0, len(square_dist_pyt_uncal)):
                sq_mittelwert_container_uncal.append(sq_mittelwert_uncal)
            

            fig, ax = plt.subplots()
            
            #x: Menge 
            #y: Distanzen
            #sq_mittelwert_container: Mittelwert
            ax.plot(x, y, 'k')
            ax.plot(x, sq_mittelwert_container_uncal, 'r')

            ax.set(xlabel='Anzahl vermessener Quadrate', ylabel='Gemessene Länge des Quadrates [Pixel]', title='Unkalibriert: Maßstab aus Schachbrettmuster')
            ax.grid()

            fig.savefig("calibration/uncalibrated_maßstab.pdf")
            plt.show()

             
            ###############################
            #Kalibrierte Vermessung 
            ###############################


            ret, corners_cal = cv2.findChessboardCorners(dev1_calibrated, (pattern_size), None)
            
            if ret == True:
                corners3 = cv2.cornerSubPix(dev1_calibrated, corners_cal,(3,3),(-1,-1),criteria) 
                imgp = [corners3]


            square_dist_cal = np.reshape(imgp, (42,2), order='C')
            square_dist_pyt_cal = []

            for i in range(1, np.size(square_dist_cal, 0)):
                dx = square_dist_cal[i,0] - square_dist_cal[i-1, 0]
                dy = square_dist_cal[i,1] - square_dist_cal[i-1, 1]

                square_dist_pyt_cal.append(math.sqrt(dx**2 + dy**2))
               
                #print('dx: ',i, dx, 'dy ', dy, '\t', square_dist_pyt_cal[i-1])

            max_square_dist_cal = square_dist_pyt_cal[0]*2

            for el in square_dist_pyt_cal:
                if el > max_square_dist_cal:
                    square_dist_pyt_cal.remove(el)
                else:
                    pass

            #erstelle Werte für Diagramm
            x_cal = np.arange(len(square_dist_pyt_cal))
            y_cal = square_dist_pyt_cal
            sq_mittelwert_cal = sum(square_dist_pyt_cal)/len(square_dist_pyt_cal)
            print('Mittelwert (kalibrierte Kamera) :\t', sq_mittelwert_cal, ' px')

            #fülle Liste mit Mittelwerten 
            sq_mittelwert_container_cal = []
            for i in range(0, len(square_dist_pyt_cal)):
                sq_mittelwert_container_cal.append(sq_mittelwert_cal)
            

            fig, ax = plt.subplots()
            
            #x: Anzahl 
            #y: Distanzen
            #sq_mittelwert_container: Mittelwert
            ax.plot(x_cal, y_cal, 'k')
            ax.plot(x_cal, sq_mittelwert_container_cal, 'r')

            ax.set(xlabel='Anzahl vermessener Quadrate', ylabel='Gemessene Länge des Quadrates [Pixel]', title='Kalibriert: Maßstab aus Schachbrettmuster')
            ax.grid()

            fig.savefig("calibration/calibated_maßstab.pdf")
            plt.show()

                


    except KeyboardInterrupt:
        Camera0.StopLive()

        #schließe alle OpenCV-Fenster
        cv2.destroyAllWindows() 

else:
    print( "Keine Kamera gefunden")