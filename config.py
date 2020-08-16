import configparser

#erzeuge configparser
config = configparser.ConfigParser()

#config-Datei, siehe Speicherort
config_section = 'cfg'
config_file = 'config/config.properties'
config.read(config_file)



#speichere geänderte Variable
def config_update(var, value):
    config.read(config_file)
    c = open(config_file, 'w')
    config.set(config_section, var, value)
    config.write(c)
    c.close()
    print('Neuer Wert für', var, ':', value)





#KONSTANTEN
DEVICE                  =     config.get('cfg', 'device')
DEVICE_FPS              = int(config.get('cfg', 'device_fps'))
DEVICE_WIDTH            = int(config.get('cfg', 'device_width'))
DEVICE_HEIGHT           = int(config.get('cfg', 'device_height'))
MARKER_DIAMETER         = int(config.get('cfg', 'marker_diameter'))
GT_REAL_FACTOR          = float(config.get('cfg', 'gt_real_factor'))


#VARIABLEN
db_basedir              =     config.get('cfg', 'db_basedir')
roi_height              = int(config.get('cfg', 'roi_height'))
denoise                 = int(config.get('cfg', 'denoise'))
lower_thresh            = int(config.get('cfg', 'lower_thresh'))

db_basedir              =     config.get('cfg', 'db_basedir')

roi_marker_x1           = int(config.get('cfg', 'roi_marker_x1'))
roi_marker_x2           = int(config.get('cfg', 'roi_marker_x2'))
roi_marker_y1           = int(config.get('cfg', 'roi_marker_y1'))
roi_marker_y2           = int(config.get('cfg', 'roi_marker_y2'))

roi_spalt_x1            = int(config.get('cfg', 'roi_spalt_x1'))
roi_spalt_x2            = int(config.get('cfg', 'roi_spalt_x2'))
roi_spalt_y1            = int(config.get('cfg', 'roi_spalt_y1'))
roi_spalt_y2            = int(config.get('cfg', 'roi_spalt_y2'))

key_calibrate           =     config.get('cfg', 'key_calibrate')

chessboard_w            = int(config.get('cfg', 'chessboard_w'))
chessboard_h            = int(config.get('cfg', 'chessboard_h'))
