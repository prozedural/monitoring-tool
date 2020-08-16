import cv2
import numpy as np
import math
import os
import glob
import time
import config
import matplotlib.pyplot as plt
import pandas as pd



#Algorithmus Einstellungen
LOWER_THRESH = config.lower_thresh 
ROI_HEIGHT = config.roi_height
DENOISE_KERNEL = config.denoise

kernel = np.ones((5,5),np.uint8)


#Umrechnungsfaktor
GT_REAL_FACTOR = config.GT_REAL_FACTOR

#realer Markerdurchmesser
MARKER_DIAMETER = config.MARKER_DIAMETER


#bereite Listen vor
img_sim_gt_set = []
img_sim_syn_set = []


list_gt_pos_left = []
list_gt_pos_right = []
list_gt_spalt = []
sum_error = 0


list_syn_pos_left = []
list_syn_pos_right = []
list_syn_spalt = []
list_syn_calc_time = []


list_gt_syn_difference = []

marker_measured_list = []
marker_average_diameter_list = []
marker_num_found_list = []


x_marker_pos_list = []
y_marker_pos_list = []
radius_marker_list = []




###################################################################################################
#wählbare Szenarien
sim_1 = 'Standard'
sim_2 = 'Sensorrauschen'
sim_3 = 'Unschärfe'
sim_4 = 'Intensität'
sim_5 = 'Vibration'


print('[1] ' + sim_1)
print('[2] ' + sim_2)
print('[3] ' + sim_3)
print('[4] ' + sim_4)
print('[5] ' + sim_5)

print()

#Benutzereingabe: wähle Simulation aus
select_simulation = int(input('[ ] Wähle Simulation: '))
print()


#Wahl der Simulation
def sim_syn_path(i):
    switcher = {
        1:'simulation_data/sim_default',
        2:'simulation_data/sim_noise',
        3:'simulation_data/sim_unsharp',
        4:'simulation_data/sim_intensity',
        5:'simulation_data/sim_vibration',

        }
    return switcher.get(i,"Falsche Eingabe")


#Liste der Ground Truth Simulationen
def sim_gt_path(i):
    switcher = {
        1:'simulation_data/sim_gt',
        2:'simulation_data/sim_gt',
        3:'simulation_data/sim_gt',
        4:'simulation_data/sim_gt',
        5:'simulation_data/sim_gt',

        }
    return switcher.get(i,"Falsche Eingabe")



img_sim_gt_dir = sim_gt_path(select_simulation)
img_sim_syn_dir = sim_syn_path(select_simulation)


#bereite Verzeichnis zum Auslesen vor
data_path = os.path.join(img_sim_gt_dir,'*.jpg')
files = glob.glob(data_path)

data_path = os.path.join(img_sim_syn_dir,'*.jpg')
files1 = glob.glob(data_path)


#berechne Framerate
max_frames = len(files)

#berechne maximale Dauer
max_duration = float(max_frames / 25)

#Informationsübersicht
print('Verzeichnis','\t', img_sim_syn_dir)
print('Framerate','\t', '25 fps')
print('max. Frames','\t', max_frames)
print('max. Dauer','\t', max_duration, 's')
print()
print('---')
print()


###################################################################################################


#Ladevorgang (Animation)
ani_symbols = "|/-\\"
ani_index = 0

def loader_ani():
    global ani_index
    print('Lese', input_frames, 'Frames', ani_symbols[ani_index % len(ani_symbols)], end="\r")
    ani_index += 1


#Benutzereingabe: wähle 0 - n Frames
while True:
    input_frames = input('Wähle Anzahl Frames < ' + str(max_frames) + ': ')
    
    #bei Eingabe "ENTER": lade alle Frames
    if input_frames == '':
        input_frames = max_frames
        break
    
    #lade n Frames
    if int(input_frames) <= max_frames:
        input_frames = int(input_frames)
        break
    
    #zu viele Frames
    else:
        print('Eingabe >', max_frames)
        continue
    

###################################################################################################
#LADE GROUND TRUTH BILDDATEN

for f1 in files[0:input_frames]:
    img_sim_gt_frame = cv2.imread(f1)

    img_sim_gt_frame = cv2.cvtColor(img_sim_gt_frame, cv2.COLOR_BGR2GRAY)
    ret, img_sim_gt_frame = cv2.threshold(img_sim_gt_frame,127,255,cv2.THRESH_BINARY)
    
    #speichere Bilddaten in Liste
    img_sim_gt_set.append(img_sim_gt_frame)
    
    loader_ani()


###################################################################################################
#LADE SYNTHETISCHE BILDDATEN

for f1 in files1[0:input_frames]:
    img_sim_frame = cv2.imread(f1)
    img_sim_frame = cv2.cvtColor(img_sim_frame, cv2.COLOR_BGR2GRAY)

    #speichere Bilddaten in Liste
    img_sim_syn_set.append(img_sim_frame)

    loader_ani()

###################################################################################################



#Bildformat, Höhe x Breite der Frames
sim_syn_h, sim_syn_w = img_sim_syn_set[0].shape 

#x,y-Mittelpunkt
sim_center_x = int(sim_syn_w / 2)
sim_center_y = int(sim_syn_h / 2)


#setze ROI
sim_roi_x = sim_syn_w
sim_roi_y = ROI_HEIGHT
sim_roi_y_half = int(sim_roi_y / 2)

print('h,w', sim_syn_h, sim_syn_w)



###################################################################################################
i = 0
while i < len(img_sim_gt_set):

    gt = img_sim_gt_set[i]
    
    #Höhe, Breite von GT
    h, w = gt.shape

    vert_center = int(h / 2)

    #setze ROI (1x hoch)
    gt_roi = gt[vert_center:vert_center + 1, 0:w]

    #check all white and all black pixel
    #prüfe alle Pixel
    #0   = schwarz
    #255 = weiß
    white_space = np.sum(gt_roi == 255)
    black_space = np.sum(gt_roi == 0)
    ctrl_sum = white_space + black_space

    #Kontrollsumme
    if (white_space + black_space) != w:
        sum_error+=1


    #ermittle Kanten (Differenzbildung der Farbwerte)
    gt_roi_u = np.array(gt_roi, dtype=np.int8) 
    dif = np.diff(gt_roi_u)

    if np.in1d(-1, dif):
        pl = np.where(dif == -1)
        gt_pos_left = pl[1][0]

    if np.in1d(1, dif):
        pr = np.where(dif == 1)
        gt_pos_right = pr[1][0]


    #AUSWERTUNG
    list_gt_pos_left.append(gt_pos_left)
    list_gt_pos_right.append(gt_pos_right)
    list_gt_spalt.append((gt_pos_right - gt_pos_left) * GT_REAL_FACTOR)

    
   


    #####################################################################################################
    #REALER ALGORITHMUS

    #Zeitstempel Start
    t0 = time.perf_counter()

    syn = img_sim_syn_set[i]
    syn_c = syn.copy()    
    
    #ROI = image[y1:y2, x1:x2]
    syn_roi = syn_c[sim_center_y - sim_roi_y_half:sim_center_y + sim_roi_y_half, 0:sim_syn_w]


    syn_roi = np.uint8(syn_roi)

    #BILDVERARBEITUNG
    blur = cv2.GaussianBlur(syn_roi,(DENOISE_KERNEL, DENOISE_KERNEL),0)
        

    ret1,thresh = cv2.threshold(blur, LOWER_THRESH, 255,cv2.THRESH_TOZERO)
    
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)


    _, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)



    bound_x, bound_y, bound_w, bound_h = cv2.boundingRect(thresh)


    syn_pos_left = bound_x
    syn_pos_right = bound_x + bound_w
    syn_width = bound_w


  

    syn_spalt = (syn_pos_right - syn_pos_left) * GT_REAL_FACTOR


    list_syn_pos_left.append(syn_pos_left)
    list_syn_pos_right.append(syn_pos_right)
    list_syn_spalt.append(syn_spalt)


    #Korrekturalgorithmus
    if i > 1:
        if list_syn_spalt[i] > list_syn_spalt[i-1]*5:
            list_syn_spalt[i] = list_syn_spalt[i-1]


    #Abweichhung Algorithmus zu Ground Truth   
    list_gt_syn_difference.append(list_gt_spalt[i] - list_syn_spalt[i])



    ###################################################################################################
    #MARKER

    #lege Kopie an
    syn_detect = img_sim_syn_set[i].copy()

    #ROI Marker = image[y1:y2, x1:x2]
    syn_detect_roi = syn_detect[0:480, 1050:1500]

    #entferne hochfrequentes Rauschen mit 7x7 Kernel
    blur = cv2.GaussianBlur(syn_detect_roi,(7,7),0)

    #konvertiere Bild in binär
    #erhöhe Kontrast
    ret,thresh_marker = cv2.threshold(blur, 0,255,cv2.THRESH_BINARY + cv2.THRESH_OTSU)



    #finde alle Konturen
    _, contours,hierarchy = cv2.findContours(thresh_marker, 1, 2)

    marker_num_found = len(contours) - 1

    marker_num_found_list.append(marker_num_found)

    #suche Kreise in den vorhandenen Konturen
    if marker_num_found > 1:
        for marker in range(0, marker_num_found):

            cnt = contours[marker]

            for cn in cnt:
                (x_marker_pos, y_marker_pos), r = cv2.minEnclosingCircle(cnt)
                
                diameter = 2 * r * GT_REAL_FACTOR
            
            #speichere alle gefundenen Durchmesser
            marker_measured_list.append(diameter)

            x_marker_pos_list.append(x_marker_pos)
            y_marker_pos_list.append(y_marker_pos)
            radius_marker_list.append(r)
            




    #ermittle Kreisdurchmesser (Mittelwert)
    average_marker_diameter = sum(marker_measured_list) / marker_num_found
    marker_average_diameter_list.append(average_marker_diameter)
    


    #setze Liste zurück
    marker_measured_list.clear()
        

    ##############################################################################################
    #setze Zeitstempel Stop
    #berechne Dauer (Start - Stop)
    dt = round((time.perf_counter() - t0), 4)
    list_syn_calc_time.append(dt)


    
    #####################################################################################################
    #####################################################################################################
    #####################################################################################################
    #####################################################################################################
    #OPENCV Fenster (Formatierung und Skalierung)
    
    
    font_size = 0.75
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_color = (0, 255,0)
    aa = cv2.LINE_AA

    syn_img_output = syn.copy()
    syn_img_output = cv2.cvtColor(syn_img_output, cv2.COLOR_GRAY2RGB)
    
    #zeichne Bounding Box
    syn_img_output = cv2.rectangle(syn_img_output, (bound_x, sim_center_y - sim_roi_y_half), (bound_x + bound_w, sim_center_y + sim_roi_y_half), (0,255,0), 2)

    #skaliere Bild auf 30%
    syn_img_output = cv2.resize(syn_img_output, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_CUBIC)



    frames_counting = format((i + 1) / 25, '.2f')
    dt_formatted = format(dt, '.4f')
    duration_formatted = format(float(input_frames / 25),'.2f')

    #füge 2 Kreise (Kante links und rechts) im GT Bild ein
    gt_out = gt.copy()
    gt_out = cv2.cvtColor(gt_out, cv2.COLOR_GRAY2RGB)
    gt_out = cv2.circle(gt_out, (gt_pos_left, sim_center_y), radius=50, color=(0, 0, 255), thickness=4)
    gt_out = cv2.circle(gt_out, (gt_pos_right, sim_center_y), radius=50, color=(0, 255, 0), thickness=4)


    #skaliere Bild auf 30%
    gt_out = cv2.resize(gt_out, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_CUBIC)

    #füge Text ein
    gt_out = cv2.putText(gt_out, str(i + 1) + '/' + str(input_frames), (20,40), font, font_size, font_color, 1, aa)
    gt_out = cv2.putText(gt_out, str(frames_counting) + '/' + str(duration_formatted) + ' s', (20,80), font, font_size, font_color, 1, aa)
    gt_out = cv2.putText(gt_out, str(dt_formatted) + ' s', (20,120), font, font_size, font_color, 1, aa)
    gt_out = cv2.putText(gt_out, str(sim_syn_w) + ' x ' + str(sim_syn_h), (20,160), font, font_size, font_color, 1, aa)


    marker_roi_out = cv2.cvtColor(thresh_marker, cv2.COLOR_GRAY2RGB)
    
    for el in range(marker_num_found):
        marker_roi_out = cv2.circle(marker_roi_out, (int(x_marker_pos_list[el]), int(y_marker_pos_list[el])), radius= int(radius_marker_list[el]), color=(0, 0, 255), thickness=2)

    marker_roi_out = cv2.resize(marker_roi_out, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_CUBIC)



    #cv2.imshow('Marker Detection view 50% ', marker_roi_out)
    cv2.imshow('Spalt Detection view 30% ', syn_img_output)
    cv2.imshow('Ground Truth view 30%', gt_out)
    cv2.waitKey(1)


    x_marker_pos_list.clear()
    y_marker_pos_list.clear()
    radius_marker_list.clear()

    prec = 4
    print('Spalt GT.', '{0:.{1}f}'.format(list_gt_spalt[i], prec), 'mm', '\t Spalt syn.', '{0:.{1}f}'.format(list_syn_spalt[i], prec), 'mm',  '\t Abweichung', '{0:.{1}f}'.format(list_gt_spalt[i] - list_syn_spalt[i], prec), 'mm')

    #setze Timer um 25fps abzuspiegel (1/25s)
    time.sleep(0.04)

    i+=1

cv2.destroyAllWindows


#####################################################################################################
#####################################################################################################
#####################################################################################################
#####################################################################################################
#MATPLOTLIB
#PLOTTE SPALT: RICHTIGER WERT, ALGORITHMUS, ABWEICHUNG


total_points = len(list_gt_pos_left)
point = np.arange(len(list_gt_pos_left))
            
#Plotgröße (Druckdatei @ 300dpi)
plot_width = 8 #inch
plot_height = 6 #inch
plot_dpi = 300

#Plotte x,y
#Argumente figsize=(width, height) in inch
plt.figure(figsize=(plot_width, plot_height))
plt.plot(point, list_gt_spalt, 'r', label='Richtiger Wert', linewidth=1)
plt.plot(point, list_syn_spalt, 'b',  label='Algorithmus', linewidth=1)
plt.plot(point, list_gt_syn_difference, 'g',  label='Abweichung', linewidth=1)

#Achsenabschnitte x,y
plt.xlim(0, 300) 
plt.ylim(0, 3) 

#Beschriftung der Achsen
plt.xlabel('Messpunkte')
plt.ylabel('Spaltbreite [mm]')
plt.title('Spaltdetektion Standard (Szenario)')

plt.grid(True)
plt.legend(loc='best')
#Speichere Plot
#plt.savefig('simulation_plots/Prozessueberwachung_Simulation_' + str(select_simulation) + '.png', dpi=plot_dpi)
plt.show()